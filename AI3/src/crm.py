"""
crm.py - Customer and ticket CRUD and lifecycle management (Module 1)

Sets up the SQLite database via SQLAlchemy, defines the Customer and
Ticket tables, and provides the CRUD functions every other module
(agents, cohort, heart, api) builds on top of.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

engine = create_engine("sqlite:///data/crm.db", echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    industry = Column(String)
    tier = Column(String, default="basic")
    signup_date = Column(DateTime, default=datetime.utcnow)
    engagement_score = Column(Integer, default=0)

    tickets = relationship("Ticket", back_populates="customer")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    priority = Column(String, default="medium")
    status = Column(String, default="Open")  # Open -> In Progress -> Escalated -> Resolved -> Closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="tickets")


Base.metadata.create_all(engine)


def add_customer(name, email, industry=None, tier="basic"):
    session = SessionLocal()
    customer = Customer(name=name, email=email, industry=industry, tier=tier)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    session.close()
    return customer


def add_ticket(customer_id, title, description, category=None, priority="medium"):
    session = SessionLocal()
    ticket = Ticket(customer_id=customer_id, title=title, description=description,
                     category=category, priority=priority)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    session.close()
    return ticket


def update_ticket_status(ticket_id, new_status):
    valid_statuses = ["Open", "In Progress", "Escalated", "Resolved", "Closed"]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status: {new_status}")

    session = SessionLocal()
    ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket:
        ticket.status = new_status
        session.commit()
        session.refresh(ticket)
    session.close()
    return ticket
