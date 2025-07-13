from Agent.nodes import Nodes
from Agent.router import context_router_node, main_router_fn
from langgraph.graph import END, START, StateGraph
from redis import Redis
from Schemas.schemas import State
from sqlalchemy.orm import Session


class Graph:
    def __init__(self, state: State, r: Redis, db: Session):
        self.n = Nodes(state=state, r=r, db=db)
        self.state = state
        self.db = db

    def build_graph(self, state: State):
        builder = StateGraph(State)
        builder.add_node("Main Router", lambda state: state)
        builder.add_node("Context Router", context_router_node)
        builder.add_node("Bot", self.n.bot_node())
        builder.add_node("Tathya", self.n.tathya_node())
        builder.add_node("Create Session", self.n.create_session_node())
        builder.add_node("Select Session", self.n.select_session_node())
        builder.add_node("Load Memory", self.n.load_memory_node())
        builder.add_node("Menu", self.n.menu_node())

        builder.set_entry_point("Main Router")
        builder.add_conditional_edges(
            "Main Router",
            main_router_fn,
            {
                "menu": "Menu",
                "select session": "Select Session",
                "create session": "Create Session",
                "load memory": "Load Memory",
                "end": END,
                "context router": "Context Router",
                "main router": "Main Router",
            },
        )
        builder.add_conditional_edges(
            "Context Router",
            lambda state: "Tathya" if state["query"] else "Bot",
            {"Tathya": "Tathya", "Bot": "Bot"},
        )
        builder.add_edge("Tathya", "Bot")
        builder.add_edge("Bot", "Main Router")
        builder.add_edge("Select Session", "Main Router")
        builder.add_edge("Create Session", "Main Router")
        builder.add_edge("Load Memory", "Main Router")
        builder.add_edge("Menu", "Main Router")

        graph = builder.compile()
        return graph
