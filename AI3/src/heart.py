"""
heart.py - HEART framework metric computation and aggregation (Module 4)

Computes the five Google HEART dimensions (Happiness, Engagement,
Adoption, Retention, Task Success) directly from live CRM data.
"""

from src.crm import SessionLocal, Customer, Ticket
from src.memory import Memory


def compute_heart_metrics():
    session = SessionLocal()
    customers = session.query(Customer).all()
    tickets = session.query(Ticket).all()
    memories = session.query(Memory).all()
    session.close()

    total_customers = len(customers)
    total_tickets = len(tickets)

    # Happiness: average customer engagement score, used as a CSAT proxy
    happiness = round(sum(c.engagement_score for c in customers) / total_customers, 2)

    # Engagement: % of customers who have raised at least one ticket
    active_customers = len(set(t.customer_id for t in tickets))
    engagement = round((active_customers / total_customers) * 100, 2)

    # Adoption: % of customers who have at least one AI-assisted interaction
    ai_assisted = len(set(m.customer_id for m in memories))
    adoption = round((ai_assisted / total_customers) * 100, 2)

    # Retention (proxy) and Task Success: resolution rate across all tickets
    resolved = len([t for t in tickets if t.status in ["Resolved", "Closed"]])
    retention_proxy = round((resolved / total_tickets) * 100, 2) if total_tickets else 0
    task_success = round((resolved / total_tickets) * 100, 2) if total_tickets else 0

    return {
        "Happiness": happiness,
        "Engagement": engagement,
        "Adoption": adoption,
        "Retention": retention_proxy,
        "Task_Success": task_success,
    }
