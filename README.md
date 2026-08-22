# RazorRescue

**Cross-rail failure recovery, conversational dunning, and churn-shielding for Razorpay recurring payments.**

RazorRescue sits on top of Razorpay's payment.failed webhook to recover involuntary payment failures (the 15-20% baseline failure rate on UPI AutoPay, SaaS subscriptions, and digital mandates) - without the retry fatigue, low engagement, and chargeback risk of static email/SMS dunning.

## The Problem

- Most payment failures are involuntary - transient bank downtime, async NPCI mandate timeouts, end-of-month liquidity gaps - not deliberate churn.
- Recovery today relies on static, one-way dunning and same-rail retries that keep failing if the issuing bank is degraded.
- Unstructured customer replies (like "salary credits Friday, charge me then") are ignored by rule-based systems, leading to premature cancellations or unwanted retries.

## The Solution

1. Cross-Rail Dynamic Fallback Switcher - On transient bank/gateway errors, instantly generates a fallback 1-tap UPI Intent across an alternate VPA/app instead of retrying the same failing rail.
2. Conversational Dunning with Promise-to-Pay - A WhatsApp-style agent parses replies like "I will pay Friday", extracts the date, pauses retries, and auto-schedules a payment prompt for that exact day.
3. Sentiment-Aware Churn Shield - Detects explicit cancellation or dissatisfaction intent and immediately halts retries plus calls the merchant cancellation API.

## Architecture

```mermaid
flowchart TD
    A[Payment Failed Webhook] --> B[Webhook Gateway]
    B --> C[Error Classifier]
    C --> D[Transient Error]
    C --> E[Hard Failure]
    D --> F[Retry Scheduler]
    E --> G[UPI Fallback Link]
    G --> H[WhatsApp Message Sent]
    H --> I[Customer Reply]
    I --> J[Intent Extraction]
    J --> K[Reschedule]
    J --> L[Cancel]
    J --> M[Retry Now]
    F --> N[Recovery Ledger]
    K --> N
    L --> N
    M --> N
```## Repository Structure

```
razorrescue/
    README.md
    app/
        main.py                 - FastAPI webhook gateway and endpoints
        classifier.py           - Deterministic error classification
        celery_app.py           - Celery configuration
        retry_scheduler.py      - Adaptive backoff retry jobs
        rail_switch.py          - UPI Intent fallback generation
        dunning_agent.py        - Simulated WhatsApp send
        intent_extraction.py    - Intent and entity extraction (mocked, swappable for Claude API)
        actions.py              - Promise-to-Pay, churn, and retry-now handlers
        db.py                   - SQLAlchemy models and Postgres persistence
        config.py               - Env var loading
    data/
        generate_mock_data.py   - Generates 100 seeded mock transactions
        mock_transactions.json
    eval.py                     - Simulation comparing RazorRescue vs naive retry
    eval_results.json           - Latest eval output
    send_test_webhook.py        - Manual test: simulate payment.failed
    send_test_reply.py          - Manual test: simulate inbound WhatsApp reply
    docker-compose.yml          - Redis and Postgres
    requirements.txt
    .env                        - Config, not committed
```

## Getting Started

```bash
# 1. Install dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Start Redis and Postgres
docker-compose up -d

# 3. Create the database tables
python -c "from app.db import init_db; init_db(); print('Tables created')"

# 4. Run the API (Terminal 1)
uvicorn app.main:app --reload

# 5. Run the Celery worker (Terminal 2)
celery -A app.celery_app worker --loglevel=info --pool=solo

# 6. Test it (Terminal 3)
python send_test_webhook.py
python send_test_reply.py
```

## Evaluation (eval.py)

eval.py replays 100 seeded mock payment.failed transactions through two strategies:

- Baseline: naive same-rail retry on a fixed schedule
- RazorRescue: classify, then cross-rail fallback or conversational dunning, then intent-based reschedule, retry, or cancel

```bash
python data/generate_mock_data.py
python eval.py
```

**Actual output** (reproducible - data generation and eval are both seeded):

```
RazorRescue Evaluation, 100 transactions simulated

Baseline (naive retry):
Recovered: 44 / 100 (44.0%)
Median time-to-recovery: 2.00 days

RazorRescue:
Recovered: 54 / 100 (54.0%)
Median time-to-recovery: 0.22 days
Hard-failure recoveries (cross-rail/dunning): 24
Chargeback-risk cancellations avoided: 3

Net Lift: +10.0 percentage points recovered vs. baseline
```

*Note: Recovery probabilities used in the simulation are informed estimates based on the problem's baseline stats, not measured production data. The simulation validates the architecture and decision logic, not real-world conversion rates.*

## Tech Stack

- API/Webhooks: FastAPI, HMAC-SHA256 verification, Redis idempotency
- Queue/Scheduling: Celery + Redis (adaptive backoff, Promise-to-Pay rescheduling)
- Datastore: PostgreSQL via SQLAlchemy
- NLP/LLM: Intent and entity extraction, currently a keyword-based mock, designed to swap in the Claude API with no interface change
- Payments: Razorpay webhook model, simulated UPI Intent generation

## Status / Roadmap

**Done:**
- Webhook ingestion and idempotency
- Deterministic failure classifier
- Predictive retry scheduler (Celery, adaptive backoff)
- Cross-rail UPI Intent fallback generation
- Simulated WhatsApp dunning
- Intent extraction (mocked; real Claude API integration pending)
- Promise-to-Pay, Churn Shield, and Retry-Now action dispatch
- PostgreSQL persistence for all events
- Evaluation harness proving recovery-rate and time-to-recovery lift

**Not yet done:**
- Real Claude API integration for intent extraction
- Real WhatsApp Business API integration
- Real Razorpay sandbox integration (live UPI Intent and cancellation API)

## Disclaimer

This is a proof-of-concept built for demonstration and evaluation purposes using simulated payment and messaging data. It is not affiliated with or endorsed by Razorpay.
