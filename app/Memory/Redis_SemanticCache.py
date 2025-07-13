import faiss
from redis import Redis
from Schemas.models import ChatMessages, ChatSessions
from Schemas.schemas import Message, State
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

THRESHOLD = 1.3


def sync_db_to_cache_and_state(state: State, session_id: str, r: Redis, db: Session):
    db_msgs = (
        db.query(ChatMessages)
        .filter(ChatMessages.session_id == session_id)
        .order_by(ChatMessages.timestamp.asc())
        .all()
    )

    if not db_msgs:
        print("No messages found in DB for this session")
        return

    msgs = [
        Message(
            role=msg.role,
            content=msg.content,
            bot_type="default",
            timestamp=msg.timestamp,
        )
        for msg in db_msgs
    ]

    for idx, msg in enumerate(msgs):
        cache_key = f"semantic:{session_id}:{idx}"
        r.hset(
            cache_key,
            mapping={
                "role": msg.role,
                "content": msg.content,
                "timestamp": str(msg.timestamp),
            },
        )

    if not state["messages"]:
        last_10 = msgs[-10:] if len(msgs) >= 10 else msgs
        state["messages"].extend(last_10)
        print(f"🧠 Loaded {len(last_10)} messages into state memory.")


def retrieve_memory(all_msgs: list[Message], query: str, k=5):
    chunks: list[list[Message]] = []
    temp = []
    for msg in all_msgs:
        temp.append(msg)

        if len(temp) == 2:
            chunks.append([m for m in temp])
            temp = []

    if temp:
        chunks.append([m for m in temp])

    chunks_str = []
    for idx, msg in enumerate(chunks):
        chunks_str.append(
            "\n".join(f"{m.role.upper()}: {m.content.strip()}" for m in chunks[idx])
        )

    model = SentenceTransformer("all-MiniLM-L6-v2")
    vectors = model.encode(chunks_str)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    query_vector = model.encode([query])
    D, I = index.search(query_vector, k)

    # for i, dist in zip(I[0], D[0]):
    #     if i < len(chunks):
    #         print(f"🔍 Distance: {dist:.4f}")
    #         print(chunks_str[i])
    #         print("-" * 40)

    top_chunks = [
        chunks[i] for i, d in zip(I[0], D[0]) if i < len(chunks) and d < THRESHOLD
    ]
    return top_chunks  # Has list[[Message(...),Message(...)]]
