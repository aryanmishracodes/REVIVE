# REVIVE — Autonomous AI Revenue Recovery Agent
> **A policy-governed revenue recovery decision and execution layer for high-scale merchant and payment gateway platforms.**

---

## 1. Context & Objectives

**REVIVE** is an autonomous AI revenue recovery decision and execution layer engineered for high-scale merchant and payment gateway platforms (built for the **Razorpay AI Builder Internship 2026 — AI Revenue Recovery Track**).

Payment failures are not homogenous. A naive system executes a blunt playbook: `payment failed → retry immediately → send generic notification`. This brute-force approach burns interchange fees, exhausts finite card network retry allowances, and creates customer churn friction on permanent decline reasons (e.g., expired cards).

**REVIVE serves as the intelligent decision and execution layer** that analyzes transaction context, customer lifetime value, historical payment success patterns, and behavioral affinity to select the mathematically optimal recovery strategy—executing strictly within deterministic fintech guardrails.

---

## 2. Core Architectural Differentiator

| Dimension | Legacy Naive Retry Systems | REVIVE Autonomous Recovery Agent |
| :--- | :--- | :--- |
| **Trigger Action** | Blind, immediate retry for all failures | Contextual classification + ML recovery probability scoring |
| **Card Expiry Handling** | Retries 3 times (100% failure rate) | 0 retries; routes directly to customer payment update link |
| **Timing Logic** | Fixed arbitrary intervals (e.g. +2 hrs) | Intelligent Retry scheduled at customer's historical peak hour |
| **High-Value Governance** | Treated identical to micro-payments | Gated for Human Ops Approval (> ₹10,000 threshold) |
| **Cost Awareness** | Retries until hard gateway error | Halts recovery when probability < 15% to save merchant fees |
| **Auditability** | Opaque error logs | Complete waterfall feature weights & immutable audit trail |

---

## 3. End-to-End Pipeline

```
FAILED PAYMENT EVENT
      │
      ▼
Context Extraction (Customer, CLV, Prior Rates, TX) ──▶ ML Recovery Probability (Logistic Regression)
                                                              │
                                                              ▼
Immutable Audit Log ◀── Simulation Runtime Outcome ◀── Policy Gate (Approved / Needs Approval / Blocked)
```

---

## 4. Machine Learning & Interpretability Engine

### Why Logistic Regression over Black-Box Ensembles?
In financial risk, credit operations, and regulatory compliance, explainability is paramount. REVIVE utilizes an **L2-Regularized Logistic Regression** scoring engine (`sklearn.linear_model.LogisticRegression`) where feature coefficients map directly to mathematical log-odds contributions:

$$\text{Log-Odds} = \beta_0 + \sum_{i=1}^n \beta_i x_i \quad \Longrightarrow \quad P(\text{Recovery}) = \frac{1}{1 + e^{-\text{Log-Odds}}}$$

### ML Model Evaluation Metrics (Trained on 6,006 Records)
* **ROC-AUC**: `0.8671` (High discriminative accuracy)
* **Brier Score**: `0.1407` (Well-calibrated probabilities)
* **Training / Test Split**: 80% Train (4,804 samples), 20% Test (1,202 samples)

### Extracted Features & Interpretability
1. **`failure_reason` (One-Hot Indicators)**: Positive baseline for `NETWORK_TIMEOUT` and `AUTHENTICATION_FAILURE`; negative baseline for `CARD_EXPIRED` and `LIMIT_EXCEEDED`.
2. **`log_amount`**: Normalized log transaction value handling financial skew.
3. **`prev_payment_success_rate`**: Customer payment reliability track record.
4. **`prev_recovery_success_rate`**: Customer responsiveness to past nudges.
5. **`retry_count`**: Diminishing returns factor as retries exhaust.
6. **`churn_probability`**: Behavioral churn risk indicator.
7. **`time_affinity_score`**: Proximity of failure timestamp to customer's historical `avg_payment_hour`.

---

## 5. Agent Architecture & Backend Tools

REVIVE's agent architecture pairs real backend tool implementations with a deterministic fallback expert system guaranteeing 100% testability offline:

1. `get_transaction(tx_id)` — Fetches transaction status, amounts, and historical failure context.
2. `get_customer(customer_id)` — Extracts customer segment, CLV, tenure, and DND preferences.
3. `get_payment_history(customer_id)` — Retrieves previous transaction timelines.
4. `predict_recovery_probability(tx_id)` — Executes ML scoring and outputs waterfall weight breakdown.
5. `calculate_recovery_priority(prob, amount, churn)` — Computes operational tier (P0–P3).
6. `schedule_retry(tx_id, optimal_time)` — Schedules intelligent retry aligned with customer peak hour.
7. `generate_customer_nudge(tx_id, channel, tone)` — Generates personalized recovery messaging.
8. `send_notification(recipient, channel, payload)` — Dispatches notification through permitted channel.
9. `create_escalation(tx_id, reason, urgency)` — Generates merchant ops tickets for high-value friction.
10. `record_outcome(action_id, outcome, recovered_amount)` — Commits execution results to database.

---

## 6. Deterministic Policy & Guardrail Engine

Every recommendation flows through strict fintech guardrails before execution:
* **Rule 1 (`RULE-01-DND-COMMUNICATION-BLOCKED`)**: If `customer.opted_out == True`, all customer-facing communications are `BLOCKED`.
* **Rule 2 (`RULE-02-MAX-RETRIES-EXCEEDED`)**: If `retry_count >= 3`, additional gateway retries are `BLOCKED`.
* **Rule 3 (`RULE-03-HIGH-VALUE-GATE`)**: If `amount > ₹10,000`, status is `REQUIRES_APPROVAL` (Human-in-the-loop gate).
* **Rule 4 (`RULE-04-INVALID-RETRY-ON-EXPIRED-CARD`)**: Blind retries on `CARD_EXPIRED` are `BLOCKED`; routes only to `PAYMENT_UPDATE`.
* **Rule 5 (`RULE-05-PREVENT-LOW-PROB-OVER-RETRY`)**: If `recovery_probability < 0.15` and `retry_count >= 2`, recovery is halted (`STOP_RECOVERY`) to save fees.
* **Rule 6 (`RULE-06-AUTO-APPROVE-STANDARD`)**: Standard low-risk policy path (`AUTO_APPROVED`).

---

## 7. Comparative Benchmark (Simulated Benchmark)

Evaluated across **6,006 synthetic transactions** generated with a fixed reproducible seed (`seed=42`):

| Metric | Baseline Naive Approach | REVIVE Autonomous Agent | Net Uplift |
| :--- | :--- | :--- | :--- |
| **Total Revenue Recovered** | ₹93,83,859.07 | **₹2,00,41,252.04** | **+₹1,06,57,392.97 (+113.57%)** |
| **Transaction Recovery Rate** | 22.83% | **48.52%** | **+25.69% pts** |
| **Average Retries per TX** | 3.00 attempts | **0.67 attempts** | **-77.72% fee waste** |
| **Card Expiry Recovery Rate** | 0.0% | **54.30%** | **+54.30% pts** |
| **High-Value (>₹10k) Capture Rate** | 24.03% | **53.34%** | **+29.31% pts** |

> **Note on Evaluation Methodology**: All benchmark numbers represent empirical measurements from a deterministic simulation executed across the 6,006 synthetic dataset (`seed=42`). Transaction recovery rate measures the percentage of failed transactions successfully recovered; recovered value measures total monetary value recovered.

---

## 8. Five Core Screens

1. **Command Center (`/`)**: Overview metrics (Total Failed Value ₹4.02 Cr, Recoverable Opportunity ₹2.00 Cr, Total Recovered, Uplift +113.6%), Payment Failure Distribution table, and Live Pitch Scenarios.
2. **Transactions (`/transactions`)**: Searchable and filterable data table supporting multi-field search by Transaction ID and Customer Name, with strategy badges and recovery-likelihood indicators.
3. **Transaction Detail (`/transactions/:id`)** — *The Core Evaluation Console*:
   * Customer context, CLV, tenure, and historical peak hour affinity.
   * Recovery probability gauge & churn risk gauge.
   * **"Why did the agent choose this?"** explainability summary.
   * **ML Feature Contribution Waterfall** breakdown table with direct log-odds impact.
   * **Policy Gate Status** indicator (`APPROVED`, `REQUIRES HUMAN APPROVAL`, `BLOCKED`).
   * **Single-Cycle Re-Score & Immutable Audit Trail** with chronological local timestamps.
4. **Recovery Actions (`/actions`)**: Controlled autonomy queue with operational summary metrics and one-click **Approve** and **Reject** governance.
5. **Strategy Simulator (`/simulator`)**: Live comparative benchmark runner (Naive Baseline vs. REVIVE) with 1-click **Reset Demo States** and **Re-Run Simulation**.

---

## 9. Six Pinned Pitch Demo Scenarios

| Scenario ID | Transaction Name | Failure Context | Strategy & Guardrail Behavior |
| :--- | :--- | :--- | :--- |
| `TX-DEMO-001` | **High-Value Recoverable** | ₹18,500, Insufficient Funds | Triggers **Human Approval Gate** due to amount > ₹10k threshold. |
| `TX-DEMO-002` | **Temporary Bank Failure** | ₹2,400, Network Timeout | Schedules **Intelligent Retry** aligned with customer's historical peak window. |
| `TX-DEMO-003` | **Card Expiry Case** | ₹4,999, Card Expired | Policy blocks blind retries; routes to **Payment Update Link**. |
| `TX-DEMO-004` | **Low Probability Drop** | ₹890, Bank Declined | **Stops Recovery** after exhausted retries to eliminate fee waste. |
| `TX-DEMO-005` | **Opted-Out Customer** | ₹1,200, Auth Failure | Policy blocks customer messaging (DND); executes silent retry. |
| `TX-DEMO-006` | **Already Recovered** | ₹6,500, Insufficient Funds | Displays full immutable audit and capture trail in `RECOVERED` state. |

---

## 10. Quick Start & Local Setup

### Prerequisites
* Python 3.11+
* Node.js v18+ & npm

### Installation & Execution (Zero-Friction Local Run)

```bash
# 1. Clone repository
git clone https://github.com/aryanmishracodes/REVIVE.git
cd REVIVE

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Seed SQLite Database & Train ML Model
python -m backend.seed

# 4. Build Frontend Assets
cd frontend
npm install
npm run build
cd ..

# 5. Start Application Server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open your browser at **`http://127.0.0.1:8000`** to access the complete application.

---

## 11. 5-Minute Panel Pitch Demo Script

1. **Minute 1 — The Problem & Command Center**:
   * Open `http://127.0.0.1:8000`.
   * *"This merchant portfolio has ₹4.02 Cr in failed payments. Traditional systems blindly retry everything 3 times—burning interchange fees and spamming customers."*
2. **Minute 2 — The Evaluation Console (`TX-DEMO-001`)**:
   * Click into `TX-DEMO-001` (₹18,500).
   * Show Customer Context (CLV: ₹2.45L, 96% past success).
   * Show **"Why did the agent choose this?"** plain-language explanation and the ML feature contribution waterfall.
   * Highlight **Policy Gate: REQUIRES_APPROVAL (`RULE-03-HIGH-VALUE-GATE`)**.
3. **Minute 3 — Controlled Autonomy & Approvals**:
   * Click **Approve Action** → transitions to `APPROVED` and reveals `[Execute Action]`.
   * Click **Execute Action** → transitions to `APPROVED & EXECUTED`, marking transaction as `Recovered`.
   * Show the clean chronological audit trail and navigate to **Recovery Actions** queue.
4. **Minute 4 — Card Expiry & Edge Cases (`TX-DEMO-003`)**:
   * Open `TX-DEMO-003` (Card Expired).
   * Show that blind retries are blocked by policy; routed to a 1-click update link.
5. **Minute 5 — Strategy Simulator Benchmark**:
   * Open **Strategy Simulator**.
   * Run benchmark: *"REVIVE delivers +113.57% net revenue uplift (+₹1.07 Cr) and saves 77.7% in wasted gateway attempts across 6,006 transactions."*
   * Close: *"REVIVE doesn't just retry failed payments—it decides what action makes sense, enforces strict financial guardrails, and provides full mathematical explainability."*

---

## 12. Project Structure

```
REVIVE/
├── backend/
│   ├── main.py                  # FastAPI app & static SPA server
│   ├── seed.py                  # Database seed & demo fixture generator
│   ├── core/                    # Config & SQLite database session
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic schemas
│   ├── ml/                      # Logistic Regression model & feature pipeline
│   ├── agent/                   # 10 Backend Tools & Policy Engine
│   └── simulator/               # Baseline vs. REVIVE benchmark engine
├── frontend/
│   ├── src/
│   │   ├── pages/               # 5 Locked Screens
│   │   ├── components/          # MetricCards, Badges, Layout
│   │   └── api/                 # Axios client
│   └── package.json
├── tests/
│   └── test_backend.py          # Pytest suite
├── pytest.ini                   # Pytest testpath configuration
├── requirements.txt             # Python dependencies
└── README.md
```

---

## 13. License

MIT License — Built for the Razorpay AI Builder Internship 2026.
