"""LangGraph orchestration with RAG, order lookup, memory and guardrails."""

import json
import re
from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

from .rag import RAG
from .tools import check_order_status
from .guardrails import input_guard
from .schema import validate_response


ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "data" / "memory.json"

rag = RAG()


class State(TypedDict, total=False):
    query: str
    thread_id: str
    masked_query: str
    allowed: bool
    guardrail: str
    route: str
    rag_result: dict
    order_result: dict
    history: list
    response: dict


def load_memory():
    """Load conversation memory as a dictionary keyed by thread ID."""
    if MEMORY.exists():
        data = json.loads(MEMORY.read_text())

        # Older memory files may contain a list.
        # Convert that safely to an empty dictionary.
        if isinstance(data, dict):
            return data

        return {}

    return {}


def save_memory(mem):
    """Persist conversation memory to JSON."""
    MEMORY.parent.mkdir(parents=True, exist_ok=True)
    MEMORY.write_text(json.dumps(mem, indent=2))


def guard_node(s):
    """Mask PII and detect prompt injection."""
    masked, ok, msg = input_guard(s["query"])

    return {
        "masked_query": masked,
        "allowed": ok,
        "guardrail": msg or "input_ok",
    }


def route_node(s):
    """Route order-related requests to the order tool, otherwise use RAG."""
    q = s["masked_query"].lower()

    return {
        "route": (
            "order_status"
            if re.search(
                r"\bnyk-\d{4}\b|order\s+(status|tracking)|where\s+is\s+my\s+order",
                q,
            )
            else "rag"
        )
    }


def rag_node(s):
    """Answer knowledge-base questions using the RAG pipeline."""
    return {
        "rag_result": rag.answer(s["masked_query"])
    }


def order_node(s):
    """Look up a fabricated order by record ID."""
    ids = re.findall(
        r"NYK-\d{4}",
        s["masked_query"].upper()
    )

    if not ids:
        return {
            "order_result": {
                "error": (
                    "Please provide a valid fabricated record_id "
                    "such as NYK-0001."
                )
            }
        }

    try:
        return {
            "order_result": check_order_status(ids[0])
        }
    except KeyError as e:
        return {
            "order_result": {
                "error": str(e)
            }
        }


def memory_node(s):
    """Persist the latest masked user query for the conversation thread."""
    mem = load_memory()

    key = s.get("thread_id", "default")

    hist = mem.get(key, [])

    # Defensive check in case an old/corrupt memory entry is not a list.
    if not isinstance(hist, list):
        hist = []

    hist.append(
        {
            "user": s["masked_query"]
        }
    )

    # Keep only the most recent 10 messages.
    mem[key] = hist[-10:]

    save_memory(mem)

    return {
        "history": hist[-10:]
    }


def response_node(s):
    """Build and validate the final response."""
    if not s.get("allowed"):
        obj = {
            "answer": (
                "I can't process that request because a "
                "prompt-injection pattern was detected."
            ),
            "route": "blocked",
            "sources": [],
            "escalation_score": None,
            "guardrail": s["guardrail"],
        }

    elif s["route"] == "order_status":
        r = s["order_result"]

        if "error" in r:
            ans = r["error"]
            score = None

        else:
            ans = (
                f"Order {r['record_id']} is {r['status']}. "
                f"Order value: INR {r['order_value_inr']}. "
                f"Escalation score: {r['escalation_score']:.3f}."
            )

            if r["escalation_score"] >= 0.70:
                ans += " Recommended for escalation."

            score = r["escalation_score"]

        obj = {
            "answer": ans,
            "route": "order_status",
            "sources": ["dataset.py"],
            "escalation_score": score,
            "guardrail": s["guardrail"],
        }

    else:
        r = s["rag_result"]

        obj = {
            "answer": r["answer"],
            "route": "rag",
            "sources": r["sources"],
            "escalation_score": None,
            "guardrail": s["guardrail"],
        }

    # Validate every final response against the project schema.
    validate_response(obj)

    return {
        "response": obj
    }


def build_graph():
    """Build and compile the LangGraph workflow."""
    g = StateGraph(State)

    g.add_node("guard", guard_node)
    g.add_node("route", route_node)
    g.add_node("rag", rag_node)
    g.add_node("order", order_node)
    g.add_node("memory", memory_node)
    g.add_node("respond", response_node)

    g.set_entry_point("guard")

    g.add_edge("guard", "route")

    g.add_conditional_edges(
        "route",
        lambda s: s["route"],
        {
            "rag": "rag",
            "order_status": "order",
        },
    )

    g.add_edge("rag", "memory")
    g.add_edge("order", "memory")
    g.add_edge("memory", "respond")
    g.add_edge("respond", END)

    return g.compile()


GRAPH = build_graph()


def ask(query, thread_id="default"):
    """Run the agent for a query and return the validated response."""
    return GRAPH.invoke(
        {
            "query": query,
            "thread_id": thread_id,
        }
    )["response"]