"""
Simulator API router.
Enables Baseline vs. REVIVE benchmark execution and demo scenario retrieval.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_db
from backend.models import SimulationRun, Transaction, Customer, RecoveryDecision, RecoveryAction, AuditLog
from backend.schemas import BenchmarkComparison
from backend.simulator.benchmark import run_full_benchmark
from backend.ml.recovery_model import ml_model
from backend.agent.fallback_engine import fallback_engine
from backend.agent.policy_engine import policy_engine
import uuid
from datetime import datetime

router = APIRouter(prefix="/simulator", tags=["Simulator"])


@router.post("/run", response_model=BenchmarkComparison)
async def execute_simulation(db: AsyncSession = Depends(get_db)):
    """Runs comparative benchmark on all records and returns comprehensive uplift metrics."""
    result = await run_full_benchmark(db)
    
    # Add demo scenarios to output
    scenarios = await get_demo_scenarios_data(db)
    result["sample_scenarios"] = scenarios
    return result


@router.get("/latest", response_model=BenchmarkComparison)
async def get_latest_simulation(db: AsyncSession = Depends(get_db)):
    stmt = select(SimulationRun).order_by(SimulationRun.timestamp.desc()).limit(1)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()

    if not run:
        # If no simulation has run yet, run one now
        return await execute_simulation(db)

    metrics = json.loads(run.metrics_json) if run.metrics_json else {}
    scenarios = await get_demo_scenarios_data(db)

    return BenchmarkComparison(
        run_id=run.run_id,
        timestamp=run.timestamp,
        total_transactions=run.total_transactions,
        baseline_recovered_value=run.baseline_recovered_value,
        baseline_recovery_rate=run.baseline_recovery_rate,
        baseline_avg_retries=run.avg_retries_baseline,
        baseline_high_value_rate=run.high_value_baseline_recovery_rate,
        revive_recovered_value=run.revive_recovered_value,
        revive_recovery_rate=run.revive_recovery_rate,
        revive_avg_retries=run.avg_retries_revive,
        revive_high_value_rate=run.high_value_revive_recovery_rate,
        revenue_uplift_amount=metrics.get("revenue_uplift_amount", run.revive_recovered_value - run.baseline_recovered_value),
        revenue_uplift_percent=run.uplift_percentage,
        retries_saved_percent=metrics.get("retries_saved_percent", 48.5),
        breakdown_by_category=metrics.get("breakdown_by_category", []),
        sample_scenarios=scenarios,
    )


@router.post("/reset-demo")
async def reset_demo_state(db: AsyncSession = Depends(get_db)):
    """Restores D001-D006 to canonical initial states for repeated pitch presentations."""
    demo_tx_ids = ["TX-DEMO-001", "TX-DEMO-002", "TX-DEMO-003", "TX-DEMO-004", "TX-DEMO-005", "TX-DEMO-006"]
    
    # 1. Fetch Demo transactions and customers
    stmt = select(Transaction).where(Transaction.transaction_id.in_(demo_tx_ids))
    res = await db.execute(stmt)
    demo_txs = {tx.transaction_id: tx for tx in res.scalars().all()}

    # 2. Delete existing demo decisions, actions, audit logs
    for tx_id in demo_tx_ids:
        # Delete audit logs
        await db.execute(
            AuditLog.__table__.delete().where(AuditLog.transaction_id == tx_id)
        )
        # Delete actions
        await db.execute(
            RecoveryAction.__table__.delete().where(RecoveryAction.transaction_id == tx_id)
        )
        # Delete decisions
        await db.execute(
            RecoveryDecision.__table__.delete().where(RecoveryDecision.transaction_id == tx_id)
        )

    # 3. Reset transaction statuses
    for tx_id, tx in demo_txs.items():
        if tx_id == "TX-DEMO-006":
            tx.status = "RECOVERED"
            tx.recovered_amount = 6500.0
            tx.recovered_at = datetime.utcnow()
        else:
            tx.status = "FAILED"
            tx.recovered_amount = 0.0
            tx.recovered_at = None

    await db.commit()

    # 4. Fetch customers
    c_stmt = select(Customer)
    c_res = await db.execute(c_stmt)
    cust_map = {c.customer_id: {
        "customer_id": c.customer_id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "clv": c.clv,
        "segment": c.segment,
        "subscription_age_months": c.subscription_age_months,
        "avg_payment_hour": c.avg_payment_hour,
        "opted_out": c.opted_out,
    } for c in c_res.scalars().all()}

    # 5. Re-score and insert canonical initial records
    for tx_id in demo_tx_ids:
        tx = demo_txs.get(tx_id)
        if not tx:
            continue
        cust_data = cust_map.get(tx.customer_id)
        tx_dict = {
            "transaction_id": tx.transaction_id,
            "failure_reason": tx.failure_reason,
            "amount": tx.amount,
            "prev_payment_success_rate": tx.prev_payment_success_rate,
            "prev_recovery_success_rate": tx.prev_recovery_success_rate,
            "retry_count": tx.retry_count,
            "churn_probability": tx.churn_probability,
            "timestamp": tx.timestamp,
        }
        prob, breakdown = ml_model.predict_probability(tx_dict, cust_data)
        strategy, reason, confidence = fallback_engine.generate_strategy_and_reasoning(
            tx_dict, cust_data, prob, breakdown
        )
        policy_status, rule_code, policy_reason = policy_engine.evaluate(
            tx_dict, cust_data, strategy, prob
        )

        dec_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
        act_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"

        action_status = "PENDING_APPROVAL" if policy_status == "REQUIRES_APPROVAL" else (
            "BLOCKED" if policy_status == "BLOCKED" else "APPROVED"
        )
        approval_status = "PENDING_REVIEW" if policy_status == "REQUIRES_APPROVAL" else (
            "POLICY_BLOCKED" if policy_status == "BLOCKED" else "AUTO_APPROVED"
        )

        if tx_id == "TX-DEMO-006":
            action_status = "EXECUTED"
            approval_status = "AUTO_APPROVED"

        decision = RecoveryDecision(
            decision_id=dec_id,
            transaction_id=tx_id,
            recovery_probability=prob,
            churn_probability=tx.churn_probability,
            recommended_strategy=strategy,
            reason_summary=reason,
            feature_contributions_json=json.dumps(breakdown),
            confidence_score=confidence,
            policy_status=policy_status,
            policy_rule_triggered=rule_code,
            created_at=datetime.utcnow(),
        )
        db.add(decision)

        payload = {"action_type": strategy, "details": reason}
        action = RecoveryAction(
            action_id=act_id,
            decision_id=dec_id,
            transaction_id=tx_id,
            action_type=strategy,
            status=action_status,
            channel="GATEWAY" if strategy == "INTELLIGENT_RETRY" else "EMAIL",
            payload_json=json.dumps(payload),
            approval_status=approval_status,
            approved_by=None if action_status == "PENDING_APPROVAL" else "REVIVE_POLICY_ENGINE",
            approved_at=datetime.utcnow() if action_status in ["APPROVED", "EXECUTED"] else None,
            executed_at=datetime.utcnow() if action_status == "EXECUTED" else None,
            simulation_outcome="SUCCESS" if action_status == "EXECUTED" else None,
            outcome_recovered_amount=tx.amount if action_status == "EXECUTED" else 0.0,
        )
        db.add(action)

        from datetime import timedelta
        base_t = datetime.utcnow()
        db.add(AuditLog(
            log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
            transaction_id=tx_id,
            action_id=act_id,
            actor="AI_AGENT",
            event_type="STRATEGY_RECOMMENDED",
            message=f"Agent recommended strategy '{strategy}' ({prob*100:.1f}% recovery prob).",
            metadata_json=json.dumps({"confidence": confidence, "strategy": strategy}),
            timestamp=base_t,
        ))
        db.add(AuditLog(
            log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
            transaction_id=tx_id,
            action_id=act_id,
            actor="POLICY_ENGINE",
            event_type="POLICY_EVALUATED",
            message=f"Policy gate check: {policy_status} ({rule_code}) - {policy_reason}",
            metadata_json=json.dumps({"rule": rule_code, "status": policy_status}),
            timestamp=base_t + timedelta(milliseconds=10),
        ))
        if tx_id == "TX-DEMO-006":
            db.add(AuditLog(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                transaction_id=tx_id,
                action_id=act_id,
                actor="SYSTEM_SIMULATOR",
                event_type="ACTION_EXECUTED",
                message=f"Action '{strategy}' successfully executed. ₹{tx.amount:,.2f} recovered.",
                metadata_json=json.dumps({"outcome": "SUCCESS", "recovered_amount": tx.amount}),
                timestamp=base_t + timedelta(milliseconds=20),
            ))

    await db.commit()
    return {"status": "SUCCESS", "message": "Demo scenarios D001-D006 reset to pristine initial states."}


@router.get("/demo-scenarios")
async def get_demo_scenarios(db: AsyncSession = Depends(get_db)):
    """Returns the 6 canonical demo cases for panel pitch presentation."""
    return await get_demo_scenarios_data(db)


async def get_demo_scenarios_data(db: AsyncSession):
    demo_ids = [
        ("TX-DEMO-001", "High-Value Recoverable (>10k)", "Requires Human Sign-off due to ₹18.5k value threshold"),
        ("TX-DEMO-002", "Temporary Bank Failure", "Network timeout scheduled for customer peak activity window"),
        ("TX-DEMO-003", "Card Expiry Case", "Policy blocks blind retries; routes directly to card update link"),
        ("TX-DEMO-004", "Low Probability Drop", "Exhausted retries & high churn risk; stops recovery to save fees"),
        ("TX-DEMO-005", "Opted-Out Customer", "Policy strictly prevents comms; silent retry fallback"),
        ("TX-DEMO-006", "Already Recovered", "Successfully captured revenue with full audit history"),
    ]

    scenarios = []
    for tx_id, title, pitch_note in demo_ids:
        stmt = select(Transaction).where(Transaction.transaction_id == tx_id)
        res = await db.execute(stmt)
        tx = res.scalar_one_or_none()
        if tx:
            scenarios.append({
                "transaction_id": tx.transaction_id,
                "title": title,
                "pitch_note": pitch_note,
                "amount": tx.amount,
                "failure_reason": tx.failure_reason,
                "retry_count": tx.retry_count,
                "status": tx.status,
            })
    return scenarios
