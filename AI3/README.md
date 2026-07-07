# AI-Integrated CRM Platform (E-Cell Task 3)

An AI-native CRM platform built for a fictional E-Cell company, integrating
customer/ticket management, LLM-powered ticket summarization, an
autonomous LangGraph routing agent, per-customer memory, cohort/churn
analytics, and a HEART framework dashboard — all exposed through a
role-based FastAPI backend.

---

## Architecture & Module Breakdown

| Module | File(s) | What it does |
|---|---|---|
| 1. Customer & Ticket Management | `src/crm.py` | SQLite + SQLAlchemy CRUD, ticket lifecycle states (Open → In Progress → Escalated → Resolved → Closed) |
| 2. LLM Intelligence Layer | `src/agents.py`, `src/memory.py` | LangChain summarization chain, LangGraph ticket-routing agent, per-customer short-term memory |
| 3. Cohort Analysis Engine | `src/cohort.py` | Retention curves by signup cohort, churn probability scoring |
| 4. HEART Dashboard | `src/heart.py`, `dashboard/heart_dashboard.py` | Live computation of all 5 HEART metrics from CRM data |
| 5. Backend API | `api/app.py` | FastAPI, versioned routes under `/api/v1/`, RBAC with 4 roles, Swagger docs at `/docs` |

### Why Groq (Llama-3.1-8b-instant) instead of Gemini
The project originally used Gemini 2.5 Flash, as it's fast and free. However,
Gemini's free tier daily quota (only 20 requests/day on the account used)
was exhausted midway through dataset generation, even after implementing
exponential backoff and retry logic. To keep the project moving under a
hard deadline, the LLM provider was switched to **Groq (Llama-3.1-8b-instant
via `langchain-groq`)**, which offers a much higher free-tier rate limit and
integrates identically through LangChain's `.invoke()` interface — proving
the modular design (swapping providers required changing only the
connection setup, not any downstream logic).

### Why LangGraph for ticket routing
A single LLM call can explain a ticket, but routing requires a sequence of
decisions: classify → decide the owning team → decide whether to escalate.
LangGraph models this as a 3-node state machine (`categorize → route →
escalate`), where only the classification step needs the LLM — routing and
escalation are deterministic logic, which is faster, cheaper, and more
reliable than asking the LLM to do everything in one shot.

### Churn scoring methodology
Churn probability (0–100) is a weighted score combining:
- **Recency** (50%) — days since the customer's last ticket, capped at 180 days
- **Engagement** (30%) — inverse of the customer's engagement score
- **Activity** (20%) — a flat penalty if the customer has never raised a ticket

Retention curve is computed per signup-month cohort as the percentage of
customers active (ticket raised) within the last 90 days.

### HEART metric definitions
| Dimension | Signal used |
|---|---|
| Happiness | Average customer engagement score (CSAT proxy) |
| Engagement | % of customers who have raised at least one ticket |
| Adoption | % of customers who have at least one AI-assisted (memory-backed) interaction |
| Retention | % of tickets resolved or closed |
| Task Success | Ticket resolution rate |

---

## Dataset

- **535 customers**, generated via LLM in batches of 25, deduplicated by email against the live database before insert.
- **~1,000 support tickets**: a portion generated live via LLM (Gemini, before quota exhaustion), the remainder generated via randomized realistic templates locally (no API cost) to reliably reach the dataset minimum after the free-tier quota was exhausted mid-generation. This hybrid approach is documented here rather than hidden, as an honest tradeoff made under a hard time constraint.
- All data is ingested directly into the live SQLite database (`data/crm.db`) via the same CRUD functions used by the API — no separate import step needed.

---

## Problems Faced & How They Were Solved

This section documents the real debugging journey, since it's often the
strongest evidence of hands-on understanding.

1. **Gemini free-tier quota exhaustion** — hit a 20-requests/day cap mid
   dataset generation. Solved by switching the LLM provider to Groq via
   LangChain's provider-agnostic interface.
2. **`NameError: name 'Base' is not defined`** — caused by Colab cells
   being run out of order after a runtime restart; SQLAlchemy's `Base`
   object only exists once its setup cell has actually executed in the
   current session.
3. **`IntegrityError: UNIQUE constraint failed`** — caused by re-running
   customer/ticket generation cells and re-inserting the same test/seed
   data. Solved by checking existing emails against the database before
   inserting, and catching `IntegrityError` around each insert as a
   safety net.
4. **`TooManyRequests (429)`** — Gemini's per-minute and per-day rate
   limits were both hit during bulk generation. Solved with exponential
   backoff retries and reduced batch frequency; ultimately required
   switching providers once the daily cap (not just per-minute) was
   confirmed exhausted.
5. **`JSONDecodeError: Unterminated string`** — the LLM's JSON response
   was cut off mid-generation when batch sizes were too large. Solved by
   reducing batch size (50 → 25 per call) and wrapping JSON parsing in a
   try/except that skips a malformed batch instead of crashing the loop.
6. **ngrok `ERR_NGROK_4018` / `ERR_NGROK_105`** — ngrok now requires an
   authenticated account and a valid personal authtoken to open a tunnel.
   Solved by registering a free ngrok account and setting
   `conf.get_default().auth_token` before connecting.
7. **`RuntimeError: asyncio.run() cannot be called from a running event
   loop`** — Colab already runs its own event loop, which conflicts with
   `uvicorn.run()`'s default startup. Solved by using `uvicorn.Server` with
   `await server.serve()` instead, which cooperates with an already-running
   event loop rather than trying to start a new one.
8. **Data loss on Colab runtime restart** — `crm.db` lives on Colab's
   temporary disk and is wiped on every restart. Solved by regenerating
   the dataset in a fresh session and immediately downloading `crm.db`
   locally via `google.colab.files.download()` as a permanent backup.

---

## How to Run

```bash
pip install -r requirements.txt

# 1. Populate the database (see notebooks/ for the full data-generation notebook)
# 2. Start the API
uvicorn api.app:app --reload

# 3. Open interactive docs
# http://localhost:8000/docs
```

Set your Groq API key as an environment variable before running (never commit real keys):
```bash
export GROQ_API_KEY="keyyyyy!!!!!!!!!"
```

---

## API Endpoints (all require an `X-Role` header: Agent / Supervisor / Admin / Analytics-readonly)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/customers` | Create a customer |
| POST | `/api/v1/tickets/create` | Create a ticket |
| POST | `/api/v1/query/agent` | Memory-aware AI query |
| POST | `/api/v1/tickets/{id}/summarize` | LangChain ticket summarization |
| GET | `/api/v1/cohorts/analysis` | Combined cohort + HEART report |

---

## Screenshots

- [ ] <img width="943" height="363" alt="image" src="https://github.com/user-attachments/assets/55a74562-1631-479b-8a8c-0c6390cf0ffb" />

- [ ] <img width="919" height="151" alt="image" src="https://github.com/user-attachments/assets/fae8725a-d8c1-4753-8996-6000fbb35213" />

- [ ] <img width="839" height="113" alt="image" src="https://github.com/user-attachments/assets/29dbb631-a507-448f-b2d8-3309bdc003a3" />

- [ ] <img width="828" height="103" alt="image" src="https://github.com/user-attachments/assets/50d0cc05-2680-4fce-8d6c-06533756c83d" />

      
- [ ] <img width="823" height="131" alt="image" src="https://github.com/user-attachments/assets/fd235092-af91-4111-822c-5bc49446840a" />

   
- [ ] <img width="476" height="265" alt="image" src="https://github.com/user-attachments/assets/064f7b16-17b7-4e24-8e52-6cf4316bd45e" />

---

## Folder Structure

```
project/
├── data/            # crm.db lives here (download from Colab, place manually)
├── notebooks/        # main exploratory/build notebook (.ipynb)
├── src/
│   ├── crm.py         # customer/ticket CRUD and lifecycle
│   ├── agents.py       # LangGraph workflows and LangChain chains
│   ├── memory.py       # per-customer interaction memory
│   ├── cohort.py        # cohort segmentation, retention, churn scoring
│   └── heart.py         # HEART framework metric computation
├── api/
│   └── app.py          # FastAPI backend with all endpoint definitions
├── dashboard/
│   └── heart_dashboard.py  # HEART chart visualization
├── models/            # saved LLM configs / prompt templates (if any)
├── README.md
└── requirements.txt
```
