"""
Database seeding script for REVIVE.
Initializes tables, generates 6,000 transactions + 6 demo scenarios, and pre-scores demo decisions.
"""
import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from backend.core.database import sync_engine, Base
from backend.models import Customer, Transaction, RecoveryDecision, RecoveryAction, AuditLog, SimulationRun
from backend.ml.dataset_generator import generate_synthetic_data
from backend.ml.recovery_model import ml_model
from backend.agent.fallback_engine import fallback_engine
from backend.agent.policy_engine import policy_engine
from backend.simulator.baseline_engine import run_baseline_simulation
from backend.simulator.revive_engine import run_revive_simulation


def seed_database():
    print("[Seed Engine] Creating database tables...")
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)

    print("[Seed Engine] Generating synthetic records (6,000 transactions + demo fixtures)...")
    customers_data, transactions_data = generate_synthetic_data(num_records=6000, seed=42)

    with Session(sync_engine) as session:
        # 1. Insert Customers
        cust_map = {}
        for c in customers_data:
            cust_obj = Customer(
                customer_id=c["customer_id"],
                name=c["name"],
                email=c["email"],
                phone=c.get("phone"),
                clv=c["clv"],
                segment=c["segment"],
                subscription_age_months=c["subscription_age_months"],
                avg_payment_hour=c["avg_payment_hour"],
                opted_out=c["opted_out"],
                created_at=c["created_at"],
            )
            session.add(cust_obj)
            cust_map[c["customer_id"]] = c
        session.commit()
        print(f"[Seed Engine] Inserted {len(customers_data)} customer profiles.")

        # 2. Insert Transactions
        for tx in transactions_data:
            tx_obj = Transaction(
                transaction_id=tx["transaction_id"],
                customer_id=tx["customer_id"],
                amount=tx["amount"],
                currency=tx.get("currency", "INR"),
                timestamp=tx["timestamp"],
                payment_method=tx["payment_method"],
                failure_reason=tx["failure_reason"],
                retry_count=tx["retry_count"],
                status=tx["status"],
                recovered_amount=tx["recovered_amount"],
                recovered_at=tx.get("recovered_at"),
                prev_payment_success_rate=tx["prev_payment_success_rate"],
                prev_recovery_success_rate=tx["prev_recovery_success_rate"],
                churn_probability=tx["churn_probability"],
            )
            session.add(tx_obj)
        session.commit()
        print(f"[Seed Engine] Inserted {len(transactions_data)} transactions.")

        # 3. Pre-populate Decisions and Actions for ALL transactions across the dataset
        print(f"[Seed Engine] Running ML inference, strategy routing, and policy gating on all {len(transactions_data)} transactions...")
        demo_tx_ids = {"TX-DEMO-001", "TX-DEMO-002", "TX-DEMO-003", "TX-DEMO-004", "TX-DEMO-005", "TX-DEMO-006"}

        for tx in transactions_data:
            tx_id = tx["transaction_id"]
            cust_data = cust_map.get(tx["customer_id"])
            
            prob, breakdown = ml_model.predict_probability(tx, cust_data)
            strategy, reason, confidence = fallback_engine.generate_strategy_and_reasoning(
                tx, cust_data, prob, breakdown
            )
            policy_status, rule_code, policy_reason = policy_engine.evaluate(
                tx, cust_data, strategy, prob
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
                churn_probability=tx["churn_probability"],
                recommended_strategy=strategy,
                reason_summary=reason,
                feature_contributions_json=json.dumps(breakdown),
                confidence_score=confidence,
                policy_status=policy_status,
                policy_rule_triggered=rule_code,
                created_at=datetime.utcnow(),
            )
            session.add(decision)

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
                outcome_recovered_amount=tx["amount"] if action_status == "EXECUTED" else 0.0,
            )
            session.add(action)

            # Audit logs (created for all demo records and representative transactions)
            if tx_id in demo_tx_ids or tx_id.startswith("TX-1000"):
                session.add(AuditLog(
                    log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                    transaction_id=tx_id,
                    action_id=act_id,
                    actor="AI_AGENT",
                    event_type="STRATEGY_RECOMMENDED",
                    message=f"Agent recommended strategy '{strategy}' ({prob*100:.1f}% recovery prob).",
                    metadata_json=json.dumps({"confidence": confidence, "strategy": strategy}),
                    timestamp=datetime.utcnow(),
                ))
                session.add(AuditLog(
                    log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                    transaction_id=tx_id,
                    action_id=act_id,
                    actor="POLICY_ENGINE",
                    event_type="POLICY_EVALUATED",
                    message=f"Policy gate check: {policy_status} ({rule_code}) - {policy_reason}",
                    metadata_json=json.dumps({"rule": rule_code, "status": policy_status}),
                    timestamp=datetime.utcnow(),
                ))
                if tx_id == "TX-DEMO-006":
                    session.add(AuditLog(
                        log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                        transaction_id=tx_id,
                        action_id=act_id,
                        actor="SYSTEM_SIMULATOR",
                        event_type="ACTION_EXECUTED",
                        message=f"Action '{strategy}' successfully executed. ₹{tx['amount']:,.2f} recovered.",
                        metadata_json=json.dumps({"outcome": "SUCCESS", "recovered_amount": tx["amount"]}),
                        timestamp=datetime.utcnow(),
                    ))

        session.commit()
        print(f"[Seed Engine] Pre-scored all {len(transactions_data)} records successfully.")

        # 4. Generate initial simulation benchmark from canonical metrics
        from backend.simulator.benchmark import CANONICAL_BENCHMARK_METRICS
        canonical = CANONICAL_BENCHMARK_METRICS

        sim_run = SimulationRun(
            run_id=f"SIM-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.utcnow(),
            total_transactions=canonical["total_transactions"],
            baseline_recovered_value=canonical["baseline_recovered_value"],
            baseline_recovery_rate=canonical["baseline_recovery_rate"],
            revive_recovered_value=canonical["revive_recovered_value"],
            revive_recovery_rate=canonical["revive_recovery_rate"],
            uplift_percentage=canonical["revenue_uplift_percent"],
            avg_retries_baseline=canonical["baseline_avg_retries"],
            avg_retries_revive=canonical["revive_avg_retries"],
            high_value_baseline_recovery_rate=canonical["baseline_high_value_rate"],
            high_value_revive_recovery_rate=canonical["revive_high_value_rate"],
            metrics_json=json.dumps({
                "breakdown_by_category": canonical["breakdown_by_category"],
                "retries_saved_percent": canonical["retries_saved_percent"],
                "revenue_uplift_amount": canonical["revenue_uplift_amount"],
            }),
        )
        session.add(sim_run)
        session.commit()
        print("[Seed Engine] Generated initial baseline vs. REVIVE benchmark run.")
        print("[Seed Engine] [SUCCESS] Database seeding complete.")


if __name__ == "__main__":
    seed_database()
