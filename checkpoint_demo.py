"""Real SQLite-backed LangGraph checkpoint/resume demonstration.

Run with requirements.txt installed. The graph is deliberately interrupted before
its tool node, then resumed with the SAME thread_id and SQLite checkpointer.
Counters make it explicit that completed nodes are not executed again.
"""
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict, total=False):
    query: str
    route: str
    order_id: str
    tool_result: dict
    response: str


COUNTS = {"guard": 0, "route": 0, "tool": 0, "memory": 0, "respond": 0}


def guard(state: State):
    COUNTS["guard"] += 1
    return {"query": state["query"]}


def route(state: State):
    COUNTS["route"] += 1
    return {"route": "order_status", "order_id": "NYK-0001"}


def tool(state: State):
    COUNTS["tool"] += 1
    from app.tools import check_order_status
    return {"tool_result": check_order_status(state["order_id"])}


def memory(state: State):
    COUNTS["memory"] += 1
    path = Path("data/memory.json")
    history = []
    if path.exists():
        import json
        try:
            history = json.loads(path.read_text())
        except Exception:
            history = []
    history.append({"thread_id": "checkpoint-demo", "query": state["query"], "route": state["route"]})
    path.write_text(__import__("json").dumps(history, indent=2))
    return {}


def respond(state: State):
    COUNTS["respond"] += 1
    result = state["tool_result"]
    return {"response": f"Order {result['record_id']} is {result['status']}."}


def build_graph(checkpointer, interrupt_before=None):
    g = StateGraph(State)
    g.add_node("guard", guard)
    g.add_node("route", route)
    g.add_node("tool", tool)
    g.add_node("memory", memory)
    g.add_node("respond", respond)
    g.add_edge(START, "guard")
    g.add_edge("guard", "route")
    g.add_edge("route", "tool")
    g.add_edge("tool", "memory")
    g.add_edge("memory", "respond")
    g.add_edge("respond", END)
    return g.compile(checkpointer=checkpointer, interrupt_before=interrupt_before or [])


def main():
    Path("data").mkdir(exist_ok=True)
    db = Path("data/checkpoints.sqlite")
    if db.exists():
        db.unlink()

    COUNTS.update({k: 0 for k in COUNTS})
    config = {"configurable": {"thread_id": "checkpoint-demo"}}

    with SqliteSaver.from_conn_string(str(db)) as saver:
        interrupted = build_graph(saver, interrupt_before=["tool"])
        first = interrupted.invoke({"query": "status of my order"}, config)
        print("after interruption:", first)
        print("counts after interruption:", COUNTS)

        resumed = build_graph(saver)
        final = resumed.invoke(None, config)
        print("after resume:", final)
        print("counts after resume:", COUNTS)

    print("checkpoint database:", db)
    print("same thread resumed; guard/route stayed at 1, while tool/memory/respond completed once.")


if __name__ == "__main__":
    main()
