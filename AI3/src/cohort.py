"""
cohort.py - Cohort segmentation, retention curves, churn scoring (Module 3)

"""

import pandas as pd
from datetime import datetime
from src.crm import SessionLocal, Customer, Ticket


def compute_cohort_analysis():
    session = SessionLocal()
    customers = session.query(Customer).all()
    tickets = session.query(Ticket).all()
    session.close()

    cust_df = pd.DataFrame([{
        "id": c.id, "industry": c.industry, "tier": c.tier,
        "signup_date": c.signup_date, "engagement_score": c.engagement_score
    } for c in customers])

    tick_df = pd.DataFrame([{
        "customer_id": t.customer_id, "created_at": t.created_at, "status": t.status
    } for t in tickets])

    cust_df["cohort_month"] = pd.to_datetime(cust_df["signup_date"]).dt.to_period("M")

    ticket_counts = tick_df.groupby("customer_id").size().rename("ticket_count")
    last_ticket = tick_df.groupby("customer_id")["created_at"].max().rename("last_ticket_date")
    cust_df = cust_df.merge(ticket_counts, left_on="id", right_index=True, how="left")
    cust_df = cust_df.merge(last_ticket, left_on="id", right_index=True, how="left")
    cust_df["ticket_count"] = cust_df["ticket_count"].fillna(0)

    now = datetime.utcnow()
    cust_df["days_since_last_ticket"] = cust_df["last_ticket_date"].apply(
        lambda d: (now - d).days if pd.notnull(d) else 999
    )

    def churn_score(row):
        score = 0
        score += min(row["days_since_last_ticket"] / 180, 1) * 50
        score += (100 - row["engagement_score"]) / 100 * 30
        score += (1 if row["ticket_count"] == 0 else 0) * 20
        return round(score, 2)

    cust_df["churn_probability"] = cust_df.apply(churn_score, axis=1)

    retention_curve = cust_df.groupby("cohort_month").apply(
        lambda g: round((g["days_since_last_ticket"] < 90).mean() * 100, 2)
    ).to_dict()

    cohort_summary = cust_df.groupby(["tier", "industry"]).agg(
        avg_churn=("churn_probability", "mean"),
        customer_count=("id", "count")
    ).reset_index().to_dict(orient="records")

    return {
        "retention_curve": {str(k): v for k, v in retention_curve.items()},
        "churn_scores": cust_df[["id", "churn_probability"]].to_dict(orient="records"),
        "cohort_summary": cohort_summary,
    }
