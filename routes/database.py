from __future__ import annotations

import os
from datetime import datetime
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL missing")

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    username: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )

    first_name: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True
    )

    consented: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    consented_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

from sqlalchemy import Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    text: Mapped[str] = mapped_column(Text)  # ← rename from message to text for consistency
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # NEW fields for approve/reject timestamps
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional: relationship
    user = relationship("User", back_populates="promotions")


class AllowedChat(Base):
    __tablename__ = "allowed_chats"

    id: Mapped[int] = mapped_column(primary_key=True)

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True
    )

    title: Mapped[str | None] = mapped_column(String(255))

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
