import logging
import os
import warnings

from Agent.graph import Graph
from Core.redis_client import r
from DataBase.setup_db import SessionLocal
from Memory.Redis_SemanticCache import sync_db_to_cache_and_state
from Memory.Redis_UploadCache import (
    cache_message,
    flush_cache_to_db,
    trim_state_messages,
)
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from Schemas.schemas import Message, State

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)

warnings.filterwarnings("ignore")

console = Console()

welcome_text = Text(
    "\n🔱 Agent Vyāsa awakened.\n\n"
    "Guiding your journey through memory, knowledge, and truth.\n"
    "Speak, and I shall listen. Ask, and I shall retrieve.\n",
    justify="center",
    style="bold bright_white",
)

console.print(
    Panel(
        welcome_text,
        border_style="bright_blue",
        title="[bold bright_magenta]Welcome[/bold bright_magenta]",
        subtitle="[dim]Agent Vyāsa — CLI Interface[/dim]",
        padding=(1, 4),
    )
)

state: State = {"messages": [], "context": None, "query": None, "session_id": None}
db = SessionLocal()
ob = Graph(state=state, r=r, db=db)
graph = ob.build_graph(state=state)
commands = ["menu", "select session", "create session", "load memory", "end"]

while True:
    user_input = input("🧠 You: ")
    if state.get("session_id") is None:
        if user_input.strip().lower() not in [
            "create session",
            "select session",
            "menu",
        ]:
            print("❗ Please type 'create session' to start a chat session.")
            continue
        elif user_input.strip().lower() == "end":
            print("❌ No session active to end. Start a session first.")
            continue
    human_msg = Message(role="human", content=user_input, bot_type=None)
    state["messages"].append(human_msg)
    if user_input.lower().strip() not in commands:
        cache_message(session_id=state["session_id"], message=human_msg)
    router_counter = 0

    for step in graph.stream(state):
        node_name, new_state = list(step.items())[0]
        # print(node_name, " ", new_state)

        if node_name == "Main Router":
            router_counter += 1

        if router_counter == 2:
            state = new_state
            break

        # print(len(state["messages"]))

    if len(state["messages"]) > 20:
        trim_state_messages(state=state)

    if not state["messages"]:
        continue

    last_msg = state["messages"][-1]
    if last_msg.role == "ai":
        print("🤖 Bot:", last_msg.content)
        cache_message(session_id=state["session_id"], message=last_msg)

    key = f"session:{state['session_id']}:messages"

    if r.llen(key) >= 5:
        flush_cache_to_db(state["session_id"], db=db)
        trim_state_messages(state)
        sync_db_to_cache_and_state(
            session_id=state["session_id"], state=state, r=r, db=db
        )

    if user_input.strip().lower() == "end":
        flush_cache_to_db(session_id=state["session_id"], db=db)
        print("📦 Session saved and ended. Farewell, Seeker.")
        break
