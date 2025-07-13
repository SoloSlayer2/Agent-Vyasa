from datetime import datetime, timezone
from typing import List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["human", "ai"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class State(TypedDict):
    messages: List[Message]
    session_id: str | None
    context: str | None
    query: str|None