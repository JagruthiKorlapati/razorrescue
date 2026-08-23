# RazorRescue

**Cross-rail failure recovery, conversational dunning, and churn-shielding for Razorpay recurring payments.**

RazorRescue sits on top of Razorpay's `payment.failed` webhook to recover involuntary payment failures (the 15-20% baseline failure rate on UPI AutoPay, SaaS subscriptions, and digital mandates) — without the retry fatigue, low engagement, and chargeback risk of static email/SMS dunning.

## The Problem

- Most payment failures are involuntary — transient bank downtime, async NPCI mandate timeouts, end-of-month liquidity gaps — not deliberate churn.
- Recovery today relies on static, one-way dunning and same-rail retries that keep failing if the issuing bank is degraded.
- Unstructured customer replies (like "salary credits Friday, charge me then" or Hinglish phrases) are ignored by rule-based systems, leading to premature cancellations or unwanted retries.

## The Solution

1. **Cross-Rail Dynamic Fallback Switcher** — On transient bank/gateway errors, instantly generates a fallback 1-tap UPI Intent across an alternate VPA/app instead of retrying the same failing rail.
2. **Conversational Dunning with Promise-to-Pay** — Powered by Google Gemini, the agent parses unstructured replies (including Hinglish), extracts the promised date/timeframe, pauses retries, and auto-schedules payment collection for that exact moment.
3. **Sentiment-Aware Churn Shield** — Detects explicit cancellation or dissatisfaction intent, halts retries, and invokes the merchant cancellation workflow to protect customer goodwill.
4. **Confidence-Gated Safeguards** — Gemini-extracted intents carry confidence scores; ambiguous or low-confidence interactions route safely to `needs_review` rather than triggering destructive actions.

## Architecture

```mermaid
flowchart LR
    A[Payment Failed] --> B[Webhook Gateway]
    B --> C{Error Classifier}
    C -->|Transient / Soft| D[Retry Scheduler]
    C -->|Hard Failure| E[UPI Fallback + WhatsApp]
    E --> F[Customer Inbound Reply]
    F --> G{Gemini Intent Extraction}
    G -->|Promise to Pay >=0.6| H[Reschedule]
    G -->|Churn Intent >=0.6| I[Cancel]
    G -->|Retry Now >=0.6| J[Immediate Retry]
    G -->|< 0.6 / Ambiguous| L[Needs Review]
    D --> K[(Recovery Ledger & Audit Trail)]
    H --> K
    I --> K
    J --> K
    L --> K

Repository Structure

razorrescue/
    README.md
    app/
        main.py                 - FastAPI webhook gateway and endpoints
        classifier.py           - Deterministic error classification
        celery_app.py           - Celery configuration
        retry_scheduler.py      - Adaptive backoff retry jobs
        rail_switch.py          - UPI Intent fallback generation
        dunning_agent.py        - Simulated WhatsApp send
        intent_extraction.py    - Real Google Gemini API intent, entity, and confidence extraction
        actions.py              - Promise-to-Pay, churn, retry-now, and needs_review handlers
        db.py                   - SQLAlchemy models, ledger, and AI audit trail persistence
        config.py               - Env var loading
    data/
        generate_mock_data.py   - Generates 100 seeded mock transactions
        mock_transactions.json
    eval.py                     - Simulation comparing RazorRescue vs naive retry
    eval_results.json           - Latest eval output
    send_test_webhook.py        - Manual test: simulate payment.failed
    send_test_reply.py          - Manual test: simulate inbound WhatsApp reply
    tests/
        test_intent.py          - Mocked Gemini API unit tests (schema, Hinglish, timeout handling)
        test_classifier.py      - Deterministic error code classification tests
    docker-compose.yml          - Redis and Postgres
    requirements.txt
    .env                        - Config, not committed
Getting StartedBash# 1. Install dependencies
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
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
Evaluation (eval.py)eval.py replays 100 seeded mock payment.failed transactions through two strategies:  Baseline: Naive same-rail retry on a fixed schedule.  RazorRescue: Classify, cross-rail fallback or conversational dunning via Gemini, then intent-based reschedule, retry, or cancel.  Bashpython data/generate_mock_data.py
python eval.py
Actual output (reproducible — data generation and eval are both seeded):  RazorRescue Evaluation, 100 transactions simulated

Baseline (naive retry):
Recovered: 44 / 100 (44.0%)
Median time-to-recovery: 2.00 days

RazorRescue:
Recovered: 54 / 100 (54.0%)
Median time-to-recovery: 0.22 days
Hard-failure recoveries (cross-rail/dunning): 24
Chargeback-risk cancellations avoided: 3

Net Lift: +10.0 percentage points recovered vs. baseline
Note: Recovery probabilities used in the simulation are informed estimates based on the problem's baseline stats, not measured production data. The simulation validates the architecture and decision logic, not real-world conversion rates.  Tech StackAPI/Webhooks: FastAPI, HMAC-SHA256 verification, Redis idempotency  Queue/Scheduling: Celery + Redis (adaptive backoff, Promise-to-Pay rescheduling)  Datastore: PostgreSQL via SQLAlchemy (stores ledger and full Gemini decision audit trails)[cite: 1, 2, 3]GenAI / NLP: Google Gemini API for structured intent, entity, and confidence extraction (with safe fallback handling)  Payments: Razorpay webhook model, simulated UPI Intent generation  Status / RoadmapDone:Webhook ingestion and HMAC verification with Redis idempotency  Deterministic failure classifier for structured Razorpay error codes  Predictive retry scheduler (Celery, adaptive backoff)  Cross-rail UPI Intent fallback generation[cite: 3]Real Google Gemini API integration for intent, timeframe, and sentiment extraction  Confidence-based decision gating (confidence >= 0.6 execution vs. needs_review safe state)  Full AI decision audit trail logged in PostgreSQL[cite: 1, 2]Promise-to-Pay, Churn Shield, and Retry-Now action dispatch[cite: 3]Evaluation harness proving recovery-rate and time-to-recovery lift[cite: 3]Not yet done:Real WhatsApp Business API integration[cite: 3]Real Razorpay sandbox live UPI Intent and cancellation API execution[cite: 3]DisclaimerThis is a proof-of-concept built for demonstration and evaluation purposes using simulated payment and messaging data. It is not affiliated with or endorsed by Razorpay.[cite: 3]