"""
app.py - FastAPI backend with all CRM endpoint definitions (Module 5)

Exposes the CRM, LLM agent, memory, cohort, and HEART modules as a
versioned REST API with role-based access control (RBAC).
Run with: uvicorn api.app:app --reload
"""

import time
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from src.crm import add_customer, add_ticket, SessionLocal, Ticket
from src.memory import get_customer_memory
from src.agents import llm, summarize_ticket_with_memory
from src.cohort import compute_cohort_analysis
from src.heart import compute_heart_metrics

app = FastAPI(title="CRM AI Platform", version="1.0")

ROLES = ["Agent", "Supervisor", "Admin", "Analytics-readonly"]


def check_role(x_role: str = Header(...)):
    if x_role not in ROLES:
        raise HTTPException(status_code=403, detail="Invalid role")
    return x_role


class CustomerIn(BaseModel):
    name: str
    email: str
    industry: str = None
    tier: str = "basic"


class TicketIn(BaseModel):
    customer_id: int
    title: str
    description: str
    priority: str = "medium"


class QueryIn(BaseModel):
    customer_id: int
    query: str


@app.post("/api/v1/customers")
def create_customer(data: CustomerIn, role: str = Header(None, alias="X-Role")):
    check_role(role)
    start = time.time()
    c = add_customer(data.name, data.email, data.industry, data.tier)
    return {
        "id": c.id, "status": "created", "cohort_assignment": c.tier,
        "latency_ms": round((time.time() - start) * 1000, 2), "agent_role": role,
    }


@app.post("/api/v1/tickets/create")
def create_ticket(data: TicketIn, role: str = Header(None, alias="X-Role")):
    check_role(role)
    t = add_ticket(data.customer_id, data.title, data.description, priority=data.priority)
    return {
        "ticket_id": t.id, "category": t.category, "assigned_agent": "auto-router",
        "agent_role": role, "timestamp": str(t.created_at),
    }


@app.post("/api/v1/query/agent")
def query_agent(data: QueryIn, role: str = Header(None, alias="X-Role")):
    check_role(role)
    context = get_customer_memory(data.customer_id)
    prompt = f"Customer history: {context}\nQuery: {data.query}\nAnswer concisely."
    response = llm.invoke(prompt)
    return {"answer": response.content, "source": "memory+llm", "confidence": 0.9, "agent_id": role}


@app.post("/api/v1/tickets/{ticket_id}/summarize")
def summarize_endpoint(ticket_id: int, role: str = Header(None, alias="X-Role")):
    check_role(role)
    session = SessionLocal()
    ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
    session.close()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    summary = summarize_ticket_with_memory(ticket)
    return {"summary": summary, "key_issues": summary, "suggested_response": summary}


@app.get("/api/v1/cohorts/analysis")
def cohort_analysis_endpoint(role: str = Header(None, alias="X-Role")):
    check_role(role)
    result = compute_cohort_analysis()
    heart = compute_heart_metrics()
    return {
        "cohort_id": "all",
        "retention_curve": result["retention_curve"],
        "churn_rate": result["cohort_summary"],
        "heart_scores": heart,
    }
