import json
from datetime import datetime

import redis
from Schemas.models import ChatMessages
from Schemas.schemas import Message, State
from sqlalchemy.orm import Session

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
CACHE_LIMIT = 20


def cache_message(session_id: str, message: Message):
    key = f"session:{session_id}:messages"
    r.rpush(key, message.model_dump_json())
    r.ltrim(key, -CACHE_LIMIT, -1)


def get_latest_message(db: Session, session_id: str):
    last_msg = (
        db.query(ChatMessages)
        .filter(ChatMessages.session_id == session_id)
        .order_by(ChatMessages.timestamp.desc())
        .first()
    )
    if last_msg:
        return last_msg
    return None


def flush_cache_to_db(session_id: str, db: Session):
    if not session_id:
        print("⚠️ Skipping DB flush — session_id is None.")
        return
    key = f"session:{session_id}:messages"
    cached = r.lrange(key, 0, -1)
    last_msg = get_latest_message(db=db, session_id=session_id)
    for msg_json in cached:
        msg = json.loads(msg_json)
        upload = ChatMessages(
            session_id=session_id,
            role=msg["role"],
            content=msg["content"],
            timestamp=msg["timestamp"],
        )
        if last_msg:
            if upload.content != last_msg.content:
                db.add(upload)
        else:
            db.add(upload)
    db.commit()
    db.close()
    r.delete(key)


def trim_state_messages(state: State):
    state["messages"] = state["messages"][-CACHE_LIMIT:]
