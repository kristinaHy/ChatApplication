from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, select

from app.models import User, UserRole, create_db_and_tables, get_session
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from app.dependencies import get_current_user, require_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Chat Application API", version="1.0.0", lifespan=lifespan)

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

@app.get("/")
async def root():
    """Root endpoint for the chat application."""
    return {"message": "Welcome to Chat Application API"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/auth/signup", response_model=UserResponse)
async def signup(user: UserCreate, session: Session = Depends(get_session)):
    # Check if user already exists
    db_user = session.exec(
        select(User).where(
            (User.username == user.username) | (User.email == user.email)
        )
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Hash password and create user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value}, expires_delta=access_token_expires
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
