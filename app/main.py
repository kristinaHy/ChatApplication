import json
from collections import deque
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from time import monotonic
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user_from_token,
)
from app.dependencies import get_current_user, require_admin
from app.models import Message, User, UserRole, create_db_and_tables, engine, get_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Chat Application API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
TASK3_DEMO_PATH = Path("app/static/task3.html")
MESSAGE_RATE_LIMIT_COUNT = 5
MESSAGE_RATE_LIMIT_WINDOW_SECONDS = 10


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(room_id, []).append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket):
        room_connections = self.active_connections.get(room_id, [])
        if websocket in room_connections:
            room_connections.remove(websocket)
        if not room_connections and room_id in self.active_connections:
            del self.active_connections[room_id]

    async def broadcast(self, room_id: str, payload: dict):
        stale_connections: list[WebSocket] = []
        for connection in list(self.active_connections.get(room_id, [])):
            try:
                await connection.send_json(payload)
            except Exception:
                stale_connections.append(connection)

        for connection in stale_connections:
            self.disconnect(room_id, connection)


manager = ConnectionManager()


class MessageRateLimiter:
    def __init__(self, max_messages: int, window_seconds: int):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.user_message_times: dict[int, deque[float]] = {}

    def allow(self, user_id: int) -> tuple[bool, int]:
        now = monotonic()
        message_times = self.user_message_times.setdefault(user_id, deque())

        while message_times and now - message_times[0] >= self.window_seconds:
            message_times.popleft()

        if len(message_times) >= self.max_messages:
            retry_after = max(
                1, int(self.window_seconds - (now - message_times[0])) + 1
            )
            return False, retry_after

        message_times.append(now)
        return True, 0


rate_limiter = MessageRateLimiter(
    max_messages=MESSAGE_RATE_LIMIT_COUNT,
    window_seconds=MESSAGE_RATE_LIMIT_WINDOW_SECONDS,
)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.USER


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


def require_non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} is required",
        )
    return normalized


def serialize_message(message: Message) -> dict:
    return {
        "id": message.id,
        "room_id": message.room_id,
        "user_id": message.user_id,
        "username": message.username,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def load_room_history(
    session: Session, room_id: str, cursor: Optional[int] = None, limit: int = 20
) -> tuple[list[dict], Optional[int]]:
    safe_limit = max(1, min(limit, 50))
    statement = select(Message).where(Message.room_id == room_id)

    if cursor is not None:
        statement = statement.where(Message.id < cursor)

    statement = statement.order_by(Message.id.desc()).limit(safe_limit + 1)
    results = list(session.exec(statement).all())

    has_more = len(results) > safe_limit
    if has_more:
        results = results[:safe_limit]

    results.reverse()
    next_cursor = results[0].id if has_more and results else None
    return [serialize_message(message) for message in results], next_cursor


def extract_message_content(raw_text: str) -> str:
    content = raw_text

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            content = str(parsed.get("content", ""))
    except json.JSONDecodeError:
        content = raw_text

    return content.strip()


@app.get("/")
async def root():
    """Root endpoint for the chat application."""
    return {"message": "Welcome to Chat Application API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/task3", response_class=FileResponse)
async def task3_demo():
    """Browser demo page for Task 3 WebSocket chat testing."""
    return FileResponse(TASK3_DEMO_PATH)


@app.post("/auth/signup", response_model=UserResponse)
async def signup(user: UserCreate, session: Session = Depends(get_session)):
    username = require_non_empty(user.username, "username")
    email = require_non_empty(user.email, "email")
    password = require_non_empty(user.password, "password")

    db_user = session.exec(
        select(User).where((User.username == username) | (User.email == email))
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    hashed_password = get_password_hash(password)
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=user.role,
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.post("/auth/login", response_model=Token)
async def login(request: Request, session: Session = Depends(get_session)):
    username: Optional[str] = None
    password: Optional[str] = None
    content_type = request.headers.get("content-type", "").lower()

    if "application/json" in content_type:
        payload = LoginRequest.model_validate(await request.json())
        username = payload.username
        password = payload.password
    else:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")

    username = require_non_empty(str(username or ""), "username")
    password = require_non_empty(str(password or ""), "password")

    user = authenticate_user(username, password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/protected/admin")
async def admin_only(current_user: User = Depends(require_admin)):
    """Protected route that requires admin role."""
    return {"message": f"Hello {current_user.username}, you are an admin!"}


@app.get("/protected/user")
async def user_or_admin(current_user: User = Depends(get_current_user)):
    """Protected route accessible to any authenticated user."""
    return {"message": f"Hello {current_user.username}, you are authenticated!"}


@app.get("/debug/routes")
def list_routes():
    return [{"path": r.path, "name": getattr(r, 'name', 'N/A'), "methods": getattr(r, 'methods', 'N/A')} for r in app.routes]


@app.websocket("/ws/{room_id}")
async def websocket_chat(
    websocket: WebSocket,
    room_id: str,
    cursor: Optional[int] = None,
    limit: int = 20,
):
    token = websocket.query_params.get("token")
    raw_cursor = websocket.query_params.get("cursor")
    raw_limit = websocket.query_params.get("limit")

    if raw_cursor is not None:
        try:
            cursor = int(raw_cursor)
        except ValueError:
            cursor = None

    if raw_limit is not None:
        try:
            limit = int(raw_limit)
        except ValueError:
            limit = 20

    await websocket.accept()

    if not token:
        await websocket.send_json({"type": "error", "detail": "Missing token"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    with Session(engine) as session:
        try:
            user = get_user_from_token(token, session)
        except (JWTError, ValueError):
            await websocket.send_json({"type": "error", "detail": "Invalid or expired token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if user is None:
            await websocket.send_json({"type": "error", "detail": "User not found for token"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        history, next_cursor = load_room_history(session, room_id, cursor, limit)

        manager.active_connections.setdefault(room_id, []).append(websocket)
        await websocket.send_json(
            {
                "type": "history",
                "room_id": room_id,
                "messages": history,
                "next_cursor": next_cursor,
            }
        )

        try:
            while True:
                raw_text = await websocket.receive_text()
                content = extract_message_content(raw_text)

                if not content:
                    await websocket.send_json(
                        {"type": "error", "detail": "Message content cannot be empty"}
                    )
                    continue

                allowed, retry_after = rate_limiter.allow(user.id)
                if not allowed:
                    await websocket.send_json(
                        {
                            "type": "rate_limit",
                            "detail": (
                                "Rate limit exceeded. "
                                f"Max {MESSAGE_RATE_LIMIT_COUNT} messages per "
                                f"{MESSAGE_RATE_LIMIT_WINDOW_SECONDS} seconds."
                            ),
                            "retry_after_seconds": retry_after,
                        }
                    )
                    continue

                db_message = Message(
                    room_id=room_id,
                    user_id=user.id,
                    username=user.username,
                    content=content,
                )
                session.add(db_message)
                session.commit()
                session.refresh(db_message)

                await manager.broadcast(
                    room_id,
                    {"type": "message", "room_id": room_id, "message": serialize_message(db_message)},
                )
        except WebSocketDisconnect:
            manager.disconnect(room_id, websocket)
        except Exception:
            manager.disconnect(room_id, websocket)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
