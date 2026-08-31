"""
Agent Orchestrator Loop.
Coordinates context gathering, ML scoring, reasoning, policy gating, action staging, and audit logging.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import Transaction, Customer, RecoveryDecision, RecoveryAction, AuditLog
from backend.agent.tools import (
    get_transaction,
    get_customer,
    get_payment_history,
    predict_recovery_probability,
    calculate_recovery_priority,
    schedule_retry,
    generate_customer_nudge,
    create_escalation,
)
from backend.agent.policy_engine import policy_engine
from backend.agent.fallback_engine import fallback_engine
from backend.core.config import settings


class AgentRunner:
    async def analyze_and_decide(
        self,
        db: AsyncSession,
        tx_id: str,
        actor: str = "AI_AGENT"
    ) -> Dict[str, Any]:
        """
        Executes full recovery pipeline for a given transaction.
        """
        # Step 1: Tool calls for context gathering
        tx_data = await get_transaction(db, tx_id)
        if not tx_data:
            raise ValueError(f"Transaction {tx_id} not found")
        cust_data = await get_customer(db, tx_data["customer_id"])

        # Step 2: ML Model Scoring with Waterfall
        ml_result = await predict_recovery_probability(db, tx_id)
        recovery_prob = ml_result["recovery_probability"]
        breakdown = ml_result["feature_breakdown"]

        # Step 3: Strategy Selection & Reasoning (Deterministic Fallback / LLM)
        strategy, reason_summary, confidence = fallback_engine.generate_strategy_and_reasoning(
            tx_data, cust_data, recovery_prob, breakdown
        )

        # Step 4: Policy & Guardrail Gate Check
        policy_status, rule_code, policy_reason = policy_engine.evaluate(
            tx_data, cust_data, strategy, recovery_prob
        )

        # Check if this is a re-score / re-analysis
        dec_check = await db.execute(select(RecoveryDecision).where(RecoveryDecision.transaction_id == tx_id))
        existing_decs = dec_check.scalars().all()
        is_rescore = len(existing_decs) > 0

        if is_rescore:
            # Clear previous cycle's records so the visible audit trail represents only the current evaluation cycle
            await db.execute(AuditLog.__table__.delete().where(AuditLog.transaction_id == tx_id))
            await db.execute(RecoveryAction.__table__.delete().where(RecoveryAction.transaction_id == tx_id))
            await db.execute(RecoveryDecision.__table__.delete().where(RecoveryDecision.transaction_id == tx_id))

        # Save Recovery Decision for Current Cycle
        decision_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
        decision = RecoveryDecision(
            decision_id=decision_id,
            transaction_id=tx_id,
            recovery_probability=recovery_prob,
            churn_probability=tx_data.get("churn_probability", 0.15),
            recommended_strategy=strategy,
            reason_summary=reason_summary,
            feature_contributions_json=json.dumps(breakdown),
            confidence_score=confidence,
            policy_status=policy_status,
            policy_rule_triggered=rule_code,
            created_at=datetime.utcnow(),
        )
        db.add(decision)

        # Stage Action based on Strategy & Policy
        action_id = f"ACT-{uuid.uuid4().hex[:8].upper()}"
        action_status = "PENDING_APPROVAL" if policy_status == "REQUIRES_APPROVAL" else (
            "BLOCKED" if policy_status == "BLOCKED" else "APPROVED"
        )
        approval_status = "PENDING_REVIEW" if policy_status == "REQUIRES_APPROVAL" else "AUTO_APPROVED"

        payload = {}
        channel = "EMAIL"
        if strategy == "INTELLIGENT_RETRY":
            retry_data = await schedule_retry(db, tx_id)
            payload = retry_data
            channel = "GATEWAY"
        elif strategy in ["CUSTOMER_NUDGE", "PAYMENT_UPDATE"]:
            nudge_data = await generate_customer_nudge(db, tx_id, channel="EMAIL")
            payload = nudge_data
            channel = "EMAIL"
        elif strategy == "ESCALATION":
            esc_data = await create_escalation(db, tx_id, reason=reason_summary)
            payload = esc_data
            channel = "INTERNAL_OPS"
        else:
            payload = {"action": "STOP_RECOVERY", "reason": reason_summary}
            channel = "SYSTEM"

        action = RecoveryAction(
            action_id=action_id,
            decision_id=decision_id,
            transaction_id=tx_id,
            action_type=strategy,
            status=action_status,
            channel=channel,
            payload_json=json.dumps(payload),
            approval_status=approval_status,
            approved_by=None if action_status == "PENDING_APPROVAL" else "REVIVE_POLICY_ENGINE",
            approved_at=datetime.utcnow() if action_status == "APPROVED" else None,
        )
        db.add(action)

        # Create current-cycle audit logs in strict chronological order:
        # TRANSACTION_RE_SCORED -> STRATEGY_RECOMMENDED -> POLICY_EVALUATED
        now = datetime.utcnow()
        if is_rescore:
            from datetime import timedelta
            db.add(AuditLog(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                transaction_id=tx_id,
                action_id=action_id,
                actor="AI_AGENT",
                event_type="TRANSACTION_RE_SCORED",
                message=f"Transaction re-scored. Model recalculated recovery probability: {recovery_prob*100:.1f}%.",
                metadata_json=json.dumps({"confidence": confidence, "recovery_probability": recovery_prob}),
                timestamp=now,
            ))
            db.add(AuditLog(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                transaction_id=tx_id,
                action_id=action_id,
                actor="AI_AGENT",
                event_type="STRATEGY_RECOMMENDED",
                message=f"Strategy recommended: {strategy}.",
                metadata_json=json.dumps({"confidence": confidence, "strategy": strategy}),
                timestamp=now + timedelta(milliseconds=10),
            ))
            db.add(AuditLog(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                transaction_id=tx_id,
                action_id=action_id,
                actor="POLICY_ENGINE",
                event_type="POLICY_EVALUATED",
                message=f"Policy gate check: {policy_status} ({rule_code}) - {policy_reason}",
                metadata_json=json.dumps({"rule": rule_code, "status": policy_status}),
                timestamp=now + timedelta(milliseconds=20),
            ))
        else:
            from datetime import timedelta
            db.add(AuditLog(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                transaction_id=tx_id,
                action_id=action_id,
                actor="AI_AGENT",
                event_type="STRATEGY_RECOMMENDED",
                message=f"Strategy recommended: {strategy}.",
                metadata_json=json.dumps({"confidence": confidence, "strategy": strategy}),
                timestamp=now,
            ))
            db.add(AuditLog(
                log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
                transaction_id=tx_id,
                action_id=action_id,
                actor="POLICY_ENGINE",
                event_type="POLICY_EVALUATED",
                message=f"Policy gate check: {policy_status} ({rule_code}) - {policy_reason}",
                metadata_json=json.dumps({"rule": rule_code, "status": policy_status}),
                timestamp=now + timedelta(milliseconds=10),
            ))

        # Reset transaction state for the fresh cycle
        tx_stmt = select(Transaction).where(Transaction.transaction_id == tx_id)
        tx_res = await db.execute(tx_stmt)
        live_tx = tx_res.scalar_one_or_none()
        if live_tx:
            if action_status == "PENDING_APPROVAL":
                live_tx.status = "PENDING_RECOVERY"
                live_tx.recovered_amount = 0.0
                live_tx.recovered_at = None
            elif action_status == "EXECUTED":
                live_tx.status = "RECOVERED"
                live_tx.recovered_amount = live_tx.amount
                live_tx.recovered_at = now
            else:
                live_tx.status = "PENDING_RECOVERY"
                live_tx.recovered_amount = 0.0
                live_tx.recovered_at = None

        await db.commit()

        return {
            "decision_id": decision_id,
            "transaction_id": tx_id,
            "strategy": strategy,
            "recovery_probability": recovery_prob,
            "confidence": confidence,
            "reason_summary": reason_summary,
            "policy_status": policy_status,
            "rule_code": rule_code,
            "action_id": action_id,
            "action_status": action_status,
            "breakdown": breakdown,
            "payload": payload,
        }


agent_runner = AgentRunner()
