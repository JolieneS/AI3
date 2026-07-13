"""
memory.py - Per-customer interaction memory and chat history (part of Module 2)

"""

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from datetime import datetime
from src.crm import Base, engine, SessionLocal


class Memory(Base):
    __tablename__ = "memory"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)


def save_memory(customer_id, ticket_id, summary):
    session = SessionLocal()
    mem = Memory(customer_id=customer_id, ticket_id=ticket_id, summary=summary)
    session.add(mem)
    session.commit()
    session.close()


def get_customer_memory(customer_id, limit=3):
    """Returns the customer's most recent memories, newest first.
    `limit` defines the short-term context window size."""
    session = SessionLocal()
    memories = (
        session.query(Memory)
        .filter(Memory.customer_id == customer_id)
        .order_by(Memory.created_at.desc())
        .limit(limit)
        .all()
    )
    session.close()
    return [m.summary for m in memories]
