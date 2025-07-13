import uuid

from LLM.chatbot import Chatbot_Init
from Memory.Redis_SemanticCache import retrieve_memory, sync_db_to_cache_and_state
from Memory.Redis_UploadCache import flush_cache_to_db, trim_state_messages
from redis import Redis
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from Schemas.models import ChatMessages, ChatSessions
from Schemas.schemas import Message, State
from sqlalchemy.orm import Session
from Tools.Tathya import Tathya


class Nodes:
    def __init__(self, state: State, r: Redis, db: Session):
        self.state = state
        self.r = r
        self.bot = Chatbot_Init()
        self.tathya = Tathya(r=r)
        self.db = db

    def bot_node(self):
        def _bot(state: State) -> State:
            return self.bot.chatbot(state)

        return _bot

    def tathya_node(self):
        def _tathya(state: State) -> State:
            return self.tathya.tathya_provider(state=state)

        return _tathya

    def create_session_node(self):
        def create_session(state: State) -> State:
            state["messages"].pop()
            session_id = str(uuid.uuid4())
            chat_name = input("📝 Give a name to this chat: ")
            if not chat_name.strip():
                chat_name = "Untitled Chat"
            db_session = ChatSessions(session_id=session_id, title=chat_name)
            self.db.add(db_session)
            self.db.commit()

            print(f"🧾 [Session] New session created: {chat_name}")

            state = {"session_id": session_id, "messages": [], "bot_type": "default"}
            return state

        return create_session

    def select_session_node(self):
        def select_session(state: State) -> State:
            state["messages"].pop()
            sessions = (
                self.db.query(ChatSessions)
                .order_by(ChatSessions.created_at.desc())
                .all()
            )
            if not sessions:
                print(
                    "📭 No previous chat sessions found. Please type 'create session' to start a new one."
                )
                return state

            # print("\n📂 Available Chat Sessions:")
            # # print(sessions)
            # for idx, session in enumerate(sessions, 1):
            #     print(
            #         f"{idx}. Chat : {session.title} | Created at: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            #     )
            console = Console()
            session_list = Text(justify="center")
            session_list.append(
                "\n📂 Available Chat Sessions\n\n", style="bold magenta"
            )

            if sessions:
                for idx, session in enumerate(sessions, 1):
                    session_list.append(f"{idx}. ", style="bold cyan")
                    session_list.append(
                        f"Chat: {session.title}", style="bold bright_white"
                    )
                    session_list.append(
                        f" | Created at: {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n",
                        style="dim",
                    )
            else:
                session_list.append("No saved sessions found.\n", style="italic red")

            console.print(
                Panel(
                    session_list,
                    border_style="bright_blue",
                    title="[bold bright_magenta]Session History[/bold bright_magenta]",
                    subtitle="[dim]Select from existing chats[/dim]",
                    padding=(1, 4),
                )
            )

            while True:
                choice = (
                    input(
                        "🔍 Select a session by number (or type 'new' to create a new session): "
                    )
                    .strip()
                    .lower()
                )
                if choice == "new":
                    state["session_id"] = None
                    return state

                if choice.isdigit() and 1 <= int(choice) <= len(sessions):
                    selected_session = sessions[int(choice) - 1]
                    state["session_id"] = selected_session.session_id
                    if not state["messages"]:
                        sync_db_to_cache_and_state(
                            state=state,
                            session_id=state["session_id"],
                            r=self.r,
                            db=self.db,
                        )
                    return state
                else:
                    print(
                        f"Invalid Input! Pls either enter new for a new state or a number between 1-{len(sessions)}"
                    )

        return select_session

    def load_memory_node(self):
        def load_memory(state: State) -> State:
            state["messages"].pop()
            session_id = state["session_id"]
            if not session_id:
                print("❌ No session ID found in state.")
                return state

            # 1. Load messages from Redis
            all_msgs = []
            idx = 0
            while True:
                key = f"semantic:{session_id}:{idx}"
                msg_data = self.r.hgetall(key)
                if not msg_data:
                    break
                all_msgs.append(
                    Message(
                        role=msg_data["role"],
                        content=msg_data["content"],
                        bot_type="default",
                        timestamp=msg_data["timestamp"],
                    )
                )
                idx += 1

            print(f"📥 Retrieved {len(all_msgs)} semantic messages from Redis.")

            while True:
                query = input("🔎 Enter the memory you want to retrieve: ").strip()
                if query.lower() in [
                    "",
                    "end",
                    "menu",
                    "new session",
                    "select session",
                    "load memory",
                ]:
                    print("⚠️ Enter a valid memory search query (not a command).")
                else:
                    break

            top_chunks = retrieve_memory(all_msgs=all_msgs, query=query, k=5)
            if not top_chunks:
                print(f"No memory found for: {query}")
                return state

            before = len(state["messages"])
            for pair in top_chunks:
                state["messages"].extend(pair)
            after = len(state["messages"])
            print(f"🧠 Added {after - before} memory messages to state.")

            # 4. Trim if exceeds 20
            if len(state["messages"]) > 20:
                trim_state_messages(state)

            return state

        return load_memory

    def menu_node(self):
        def menu(state: State) -> State:
            state["messages"].pop()
            # print(
            #     """
            # 🔱  Welcome, Seeker. I am Agent Vyāsa — your guide through knowledge, memory, and inquiry.

            # 📜 **Available Commands**:

            # 1. 🧠 `load memory`
            #    → Recall past conversations tied to this session and infuse them into the present.

            # 2. 📂 `select session`
            #    → Choose from your previous sessions or create a new one.

            # 3. ✨ `new session`
            #    → Begin a fresh thread of conversation. A new scroll for new thoughts.

            # 4. 🔍 `Tathya: <your query>`
            #    → Invoke deep knowledge retrieval.
            #    Example → `Tathya: What happened in the Second Battle of Panipat?`
            #    Agent Vyāsa will seek context from external sources and enrich your session.

            # 5. 🧭 `menu`
            #    → Redisplay this guide. Call upon Vyāsa to remind you of your tools.

            # 6. ❌ `end`
            #    → Close the session. Memory shall rest until called upon again.

            # 🪔 Speak, and I shall listen. Ask, and I shall retrieve.
            # """
            # )
            console = Console()

            menu_text = Text(justify="center")

            menu_text.append(
                "\n🔱 Agent Vyāsa — Command Scroll\n\n", style="bold magenta"
            )

            menu_text.append("📜 Available Commands:\n\n", style="bold bright_white")

            menu_text.append("1. 🧠 load memory\n", style="bold cyan")
            menu_text.append(
                "   → Recall past conversations tied to this session.\n\n", style="dim"
            )

            menu_text.append("2. 📂 select session\n", style="bold cyan")
            menu_text.append(
                "   → Choose from your previous sessions or create a new one.\n\n",
                style="dim",
            )

            menu_text.append("3. ✨ new session\n", style="bold cyan")
            menu_text.append(
                "   → Begin a fresh thread of conversation.\n\n", style="dim"
            )

            menu_text.append("4. 🔍 Tathya: <your query>\n", style="bold cyan")
            menu_text.append(
                "   → Deep knowledge retrieval from external sources.\n", style="dim"
            )
            menu_text.append(
                "   Example: Tathya: What happened in the Second Battle of Panipat?\n\n",
                style="dim",
            )

            menu_text.append("5. 🧭 menu\n", style="bold cyan")
            menu_text.append("   → Show this command guide again.\n\n", style="dim")

            menu_text.append("6. ❌ end\n", style="bold cyan")
            menu_text.append(
                "   → End the session. Memory shall rest.\n\n", style="dim"
            )

            menu_text.append(
                "🪔 Speak, and I shall listen. Ask, and I shall retrieve.\n",
                style="italic green",
            )

            # Print inside a fancy panel
            console.print(
                Panel(
                    menu_text,
                    border_style="bright_blue",
                    title="[bold bright_magenta]Command Menu[/bold bright_magenta]",
                    subtitle="[dim]Agent Vyāsa — CLI Interface[/dim]",
                    padding=(1, 4),
                )
            )

            return state

        return menu
