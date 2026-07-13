"""
agents.py - LangGraph workflows and LangChain chain definitions (Module 2)

"""

import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict

from src.crm import update_ticket_status
from src.memory import get_customer_memory, save_memory

# API key is read from an environment variable - never hardcode real keys in source files.
llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=os.environ.get("GROQ_API_KEY"))



def summarize_ticket_with_memory(ticket):
    past_context = get_customer_memory(ticket.customer_id)
    context_text = "\n".join(past_context) if past_context else "No prior history."

    prompt = f"""You are a support ticket summarizer with memory of past interactions.

Past context for this customer:
{context_text}

New ticket:
Title: {ticket.title}
Description: {ticket.description}

Output exactly 3 lines:
Key Issue: <one line>
Urgency: <low/medium/high/urgent>
Suggested Resolution: <one line>"""

    response = llm.invoke(prompt)
    summary = response.content
    save_memory(ticket.customer_id, ticket.id, summary)
    return summary


class TicketState(TypedDict):
    ticket_id: int
    title: str
    description: str
    category: str
    priority: str
    assigned_team: str


def categorize_node(state: TicketState) -> TicketState:
    prompt = f"""Classify this support ticket.
Title: {state['title']}
Description: {state['description']}
Respond with exactly 2 words: <category>,<priority>
Category must be one of: Technical, Billing, Account, Feature Request, General
Priority must be one of: low, medium, high, urgent"""

    response = llm.invoke(prompt)
    parts = response.content.strip().split(",")
    state["category"] = parts[0].strip()
    state["priority"] = parts[1].strip()
    return state


def routing_node(state: TicketState) -> TicketState:
    team_map = {
        "Technical": "Tech Team",
        "Billing": "Finance Team",
        "Account": "Account Support",
        "Feature Request": "Product Team",
        "General": "General Support",
    }
    state["assigned_team"] = team_map.get(state["category"], "General Support")
    return state


def escalation_node(state: TicketState) -> TicketState:
    if state["priority"] in ["high", "urgent"]:
        update_ticket_status(state["ticket_id"], "Escalated")
    else:
        update_ticket_status(state["ticket_id"], "In Progress")
    return state


graph = StateGraph(TicketState)
graph.add_node("categorize", categorize_node)
graph.add_node("route", routing_node)
graph.add_node("escalate", escalation_node)

graph.set_entry_point("categorize")
graph.add_edge("categorize", "route")
graph.add_edge("route", "escalate")
graph.add_edge("escalate", END)

agent = graph.compile()
