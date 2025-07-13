import re

from Schemas.schemas import Message, State


def main_router_fn(state: State):
    try:
        if not state["messages"]:
            return "menu"
        last_msg_obj = state["messages"][-1]
        if last_msg_obj.role == "ai":
            return "main router"

        last_msg = last_msg_obj.content.lower().strip()
        COMMAND_MAP = {
            "menu": "menu",
            "select session": "select session",
            "create session": "create session",
            "load memory": "load memory",
            "end": "end",
        }

        return COMMAND_MAP.get(last_msg, "context router")
    except Exception as e:
        print("Router error:", e)
        return "menu"


def context_router_node(state: State):
    last_msg_obj = state["messages"][-1]
    last_msg = last_msg_obj.content.strip()

    match = re.match(r"^(.*?)\s*:\s*(.+)$", last_msg)

    if match:
        group1 = match.group(1).strip().lower()
        group2 = match.group(2).strip()

        # print(group1, " ", group2)

        if group1 == "tathya":
            state["query"] = group2

    return state
