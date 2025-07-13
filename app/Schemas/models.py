import datetime
import uuid
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ChatSessions(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = (PrimaryKeyConstraint("session_id", name="chat_sessions_pkey"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    title: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Untitled"
    )

    chat_messages: Mapped[List["ChatMessages"]] = relationship(
        "ChatMessages", back_populates="session"
    )


class ChatMessages(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.session_id"],
            ondelete="CASCADE",
            name="chat_messages_session_id_fkey",
        ),
        PrimaryKeyConstraint("id", name="chat_messages_pkey"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    role: Mapped[str] = mapped_column(Enum("human", "ai", name="role_type"))
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    session: Mapped["ChatSessions"] = relationship(
        "ChatSessions", back_populates="chat_messages"
    )
