from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import os
from sqlmodel import Field, Session, SQLModel, create_engine


# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chatapp.db")
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.USER)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: str = Field(index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    username: str = Field(index=True)
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
