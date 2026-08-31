"""
Comprehensive test suite for REVIVE backend.
Tests ML pipeline, Policy Engine guardrails, Simulator benchmark, Agent decision runner, and API routes.
"""
import pytest
import uuid
import json
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.main import app
from backend.core.database import AsyncSessionLocal
from backend.models import Transaction, Customer, RecoveryDecision, RecoveryAction, AuditLog
from backend.ml.dataset_generator import generate_synthetic_data, generate_demo_fixtures
from backend.ml.recovery_model import ml_model
from backend.ml.feature_pipeline import extract_features
from backend.agent.policy_engine import policy_engine
from backend.agent.fallback_engine import fallback_engine
from backend.agent.agent_runner import agent_runner
from backend.simulator.baseline_engine import run_baseline_simulation
from backend.simulator.revive_engine import run_revive_simulation


def test_dataset_generation_seed_reproducibility():
    """Verify deterministic dataset generation with fixed seed."""
    c1, t1 = generate_synthetic_data(num_records=500, seed=42)
    c2, t2 = generate_synthetic_data(num_records=500, seed=42)
    assert len(c1) == len(c2)
    assert len(t1) == len(t2)
    assert t1[0]["transaction_id"] == t2[0]["transaction_id"]
    assert t1[0]["amount"] == t2[0]["amount"]


def test_demo_fixtures_present():
    """Verify all 6 pitch demo fixtures are correctly shaped."""
    custs, txs = generate_demo_fixtures()
    assert len(txs) == 6
    tx_map = {t["transaction_id"]: t for t in txs}
    
    # 1. High value >10k
    assert tx_map["TX-DEMO-001"]["amount"] > 10000.0
    # 2. Network timeout
    assert tx_map["TX-DEMO-002"]["failure_reason"] == "NETWORK_TIMEOUT"
    # 3. Card expired
    assert tx_map["TX-DEMO-003"]["failure_reason"] == "CARD_EXPIRED"
    # 4. Low prob
    assert tx_map["TX-DEMO-004"]["retry_count"] >= 3
    # 5. Opted out
    assert tx_map["TX-DEMO-005"]["failure_reason"] == "AUTHENTICATION_FAILURE"
    # 6. Already recovered
    assert tx_map["TX-DEMO-006"]["status"] == "RECOVERED"


def test_ml_model_accuracy_and_bounds():
    """Verify ML model produces valid probabilities and feature explanations."""
    sample_tx = {
        "amount": 2500.0,
        "failure_reason": "NETWORK_TIMEOUT",
        "prev_payment_success_rate": 0.95,
        "prev_recovery_success_rate": 0.80,
        "retry_count": 0,
        "churn_probability": 0.10,
    }
    sample_cust = {"avg_payment_hour": 18}
    prob, breakdown = ml_model.predict_probability(sample_tx, sample_cust)
    
    assert 0.0 <= prob <= 1.0
    assert prob > 0.50  # Network timeout + 95% past rate should have high recovery probability
    assert len(breakdown) > 0
    # Verify breakdown contains valid weights and explanations
    for item in breakdown:
        assert "feature" in item
        assert "weight" in item
        assert "impact" in item
        assert "explanation" in item


def test_policy_engine_guardrails():
    """Test fintech policy guardrails."""
    # 1. High Value Gate (>10k)
    status, code, _ = policy_engine.evaluate(
        {"amount": 15000.0, "retry_count": 0, "failure_reason": "INSUFFICIENT_FUNDS"},
        {"opted_out": False},
        "INTELLIGENT_RETRY",
        0.85
    )
    assert status == "REQUIRES_APPROVAL"
    assert code == "RULE-03-HIGH-VALUE-GATE"

    # 2. Max Retries Exceeded (>=3)
    status, code, _ = policy_engine.evaluate(
        {"amount": 1500.0, "retry_count": 3, "failure_reason": "BANK_DECLINED"},
        {"opted_out": False},
        "INTELLIGENT_RETRY",
        0.45
    )
    assert status == "BLOCKED"
    assert code == "RULE-02-MAX-RETRIES-EXCEEDED"

    # 3. Card Expired Retry Prohibition
    status, code, _ = policy_engine.evaluate(
        {"amount": 2000.0, "retry_count": 0, "failure_reason": "CARD_EXPIRED"},
        {"opted_out": False},
        "INTELLIGENT_RETRY",
        0.70
    )
    assert status == "BLOCKED"
    assert code == "RULE-04-INVALID-RETRY-ON-EXPIRED-CARD"

    # 4. Opt-Out Communication Gate
    status, code, _ = policy_engine.evaluate(
        {"amount": 2000.0, "retry_count": 0, "failure_reason": "AUTHENTICATION_FAILURE"},
        {"opted_out": True},
        "CUSTOMER_NUDGE",
        0.80
    )
    assert status == "BLOCKED"
    assert code == "RULE-01-DND-COMMUNICATION-BLOCKED"


def test_simulator_revive_uplift_over_baseline():
    """Verify REVIVE simulator outperforms naive baseline on recovery rate and revenue."""
    _, sample_txs = generate_synthetic_data(num_records=1000, seed=42)
    base_res = run_baseline_simulation(sample_txs)
    rev_res = run_revive_simulation(sample_txs)

    assert rev_res["recovered_value"] > base_res["recovered_value"]
    assert rev_res["recovery_rate"] > base_res["recovery_rate"]
    assert rev_res["avg_retries_per_tx"] < base_res["avg_retries_per_tx"]  # Saved wasted retries


@pytest.mark.asyncio
async def test_rescore_clean_single_cycle_lifecycle():
    """Verify re-score creates clean single cycle without accumulating past events."""
    async with AsyncSessionLocal() as db:
        # Re-score TX-DEMO-001
        res = await agent_runner.analyze_and_decide(db, "TX-DEMO-001")
        assert res["transaction_id"] == "TX-DEMO-001"
        assert res["policy_status"] == "REQUIRES_APPROVAL"
        assert res["action_status"] == "PENDING_APPROVAL"

        # Check audit trail has exactly the 3 fresh cycle events
        stmt = select(AuditLog).where(AuditLog.transaction_id == "TX-DEMO-001").order_by(AuditLog.timestamp)
        db_res = await db.execute(stmt)
        logs = db_res.scalars().all()
        assert len(logs) == 3
        assert [l.event_type for l in logs] == [
            "TRANSACTION_RE_SCORED",
            "STRATEGY_RECOMMENDED",
            "POLICY_EVALUATED"
        ]


@pytest.mark.asyncio
async def test_human_approval_and_execution_lifecycle():
    """Verify human approval and execution flow for gated transaction."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Reset demo states first
        reset_res = await client.post("/api/v1/simulator/reset-demo")
        assert reset_res.status_code == 200

        # Get TX-DEMO-001 detail
        detail_res = await client.get("/api/v1/transactions/TX-DEMO-001")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["status"] in ["FAILED", "PENDING_RECOVERY"]
        assert len(detail["actions"]) > 0
        action = detail["actions"][0]
        assert action["status"] == "PENDING_APPROVAL"

        # Approve action
        approve_res = await client.post(f"/api/v1/actions/{action['action_id']}/approve")
        assert approve_res.status_code == 200
        approved_action = approve_res.json()
        assert approved_action["status"] == "APPROVED"

        # Execute action
        exec_res = await client.post(f"/api/v1/actions/{action['action_id']}/execute")
        assert exec_res.status_code == 200
        executed_action = exec_res.json()
        assert executed_action["status"] == "EXECUTED"
        assert executed_action["outcome_recovered_amount"] == detail["amount"]

        # Verify transaction status is RECOVERED and audit log contains ACTION_EXECUTED
        updated_res = await client.get("/api/v1/transactions/TX-DEMO-001")
        assert updated_res.status_code == 200
        updated = updated_res.json()
        assert updated["status"] == "RECOVERED"
        assert updated["recovered_amount"] == detail["amount"]
        event_types = [l["event_type"] for l in updated["audit_logs"]]
        assert "ACTION_APPROVED" in event_types
        assert "ACTION_EXECUTED" in event_types


@pytest.mark.asyncio
async def test_human_rejection_lifecycle():
    """Verify human rejection flow and policy gating."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Re-score TX-DEMO-001 to get fresh action
        rescore_res = await client.post("/api/v1/transactions/TX-DEMO-001/analyze")
        assert rescore_res.status_code == 200

        detail_res = await client.get("/api/v1/transactions/TX-DEMO-001")
        detail = detail_res.json()
        action = detail["actions"][0]

        # Reject action
        reject_res = await client.post(
            f"/api/v1/actions/{action['action_id']}/reject",
            json={"reason": "Declined by Merchant Ops"}
        )
        assert reject_res.status_code == 200
        rejected = reject_res.json()
        assert rejected["status"] == "REJECTED"

        # Verify cannot execute a rejected action
        exec_attempt = await client.post(f"/api/v1/actions/{action['action_id']}/execute")
        assert exec_attempt.status_code == 400

        # Verify audit log recorded ACTION_REJECTED
        updated_res = await client.get("/api/v1/transactions/TX-DEMO-001")
        updated = updated_res.json()
        assert updated["status"] != "RECOVERED"
        event_types = [l["event_type"] for l in updated["audit_logs"]]
        assert "ACTION_REJECTED" in event_types


@pytest.mark.asyncio
async def test_api_endpoints_health_and_data():
    """Verify all major API endpoints return valid, consistent data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "HEALTHY"

        # 2. Dashboard metrics
        dash = await client.get("/api/v1/dashboard/metrics")
        assert dash.status_code == 200
        d_data = dash.json()
        assert "total_failed_value" in d_data
        assert "recoverable_value" in d_data
        assert "recovered_value" in d_data
        assert "overall_recovery_rate" in d_data
        assert d_data["total_failed_count"] >= 0

        # 3. Transactions list
        txs = await client.get("/api/v1/transactions?limit=20")
        assert txs.status_code == 200
        tx_data = txs.json()
        assert isinstance(tx_data, list)
        assert len(tx_data) > 0

        # 4. Strategy simulator benchmark
        bench = await client.get("/api/v1/simulator/latest")
        assert bench.status_code == 200
        b_data = bench.json()
        assert "baseline_recovery_rate" in b_data
        assert "revive_recovery_rate" in b_data
        assert "revenue_uplift_amount" in b_data
        assert b_data["revive_recovery_rate"] > b_data["baseline_recovery_rate"]

        # 5. Demo scenarios
        demos = await client.get("/api/v1/simulator/demo-scenarios")
        assert demos.status_code == 200
        assert len(demos.json()) == 6
