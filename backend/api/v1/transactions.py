"""
Transactions API router.
Provides listing, filtering, deep context analysis, and on-demand agent decision execution.
"""
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from backend.core.database import get_db
from backend.models import Transaction, Customer, RecoveryDecision, RecoveryAction, AuditLog
from backend.schemas import (
    TransactionListResponse,
    TransactionDetailResponse,
    RecoveryDecisionResponse,
    RecoveryActionResponse,
    AuditLogResponse,
    CustomerResponse,
    FeatureWeight,
)
from backend.ml.recovery_model import ml_model
from backend.agent.fallback_engine import fallback_engine
from backend.agent.policy_engine import policy_engine
from backend.agent.agent_runner import agent_runner
from backend.agent.tools import calculate_recovery_priority

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=List[TransactionListResponse])
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    failure_reason: Optional[str] = None,
    search: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Transaction).outerjoin(
        Customer, Transaction.customer_id == Customer.customer_id
    ).options(
        selectinload(Transaction.customer),
        selectinload(Transaction.decisions)
    ).order_by(Transaction.timestamp.desc())

    if status and status != "ALL":
        stmt = stmt.where(Transaction.status == status)
    if failure_reason and failure_reason != "ALL":
        stmt = stmt.where(Transaction.failure_reason == failure_reason)
    if search and search.strip():
        search_pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            (Transaction.transaction_id.ilike(search_pattern)) |
            (Transaction.customer_id.ilike(search_pattern)) |
            (Customer.name.ilike(search_pattern))
        )

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    txs = res.scalars().all()

    response_items = []
    for t in txs:
        latest_dec = t.decisions[-1] if t.decisions else None
        if latest_dec:
            rec_prob = latest_dec.recovery_probability
            strategy = latest_dec.recommended_strategy
            policy_stat = latest_dec.policy_status
        else:
            c_data = {"avg_payment_hour": t.customer.avg_payment_hour} if t.customer else None
            tx_dict = {
                "failure_reason": t.failure_reason,
                "amount": t.amount,
                "prev_payment_success_rate": t.prev_payment_success_rate,
                "prev_recovery_success_rate": t.prev_recovery_success_rate,
                "retry_count": t.retry_count,
                "churn_probability": t.churn_probability,
                "timestamp": t.timestamp,
            }
            rec_prob, breakdown = ml_model.predict_probability(tx_dict, c_data)
            strategy, _, _ = fallback_engine.generate_strategy_and_reasoning(tx_dict, c_data, rec_prob, breakdown)
            policy_stat, _, _ = policy_engine.evaluate(tx_dict, c_data, strategy, rec_prob)

        prio = calculate_recovery_priority(rec_prob, t.amount, t.churn_probability)

        if priority and priority != "ALL" and prio != priority:
            continue

        response_items.append(TransactionListResponse(
            transaction_id=t.transaction_id,
            customer_id=t.customer_id,
            customer_name=t.customer.name if t.customer else "Unknown",
            customer_segment=t.customer.segment if t.customer else "SMB",
            amount=t.amount,
            currency=t.currency,
            timestamp=t.timestamp,
            payment_method=t.payment_method,
            failure_reason=t.failure_reason,
            retry_count=t.retry_count,
            status=t.status,
            recovered_amount=t.recovered_amount,
            recovered_at=t.recovered_at,
            prev_payment_success_rate=t.prev_payment_success_rate,
            prev_recovery_success_rate=t.prev_recovery_success_rate,
            churn_probability=t.churn_probability,
            recovery_probability=rec_prob,
            priority=prio,
            recommended_strategy=strategy,
            policy_status=policy_stat,
        ))

    return response_items


@router.get("/{tx_id}", response_model=TransactionDetailResponse)
async def get_transaction_detail(tx_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Transaction).options(
        selectinload(Transaction.customer),
        selectinload(Transaction.decisions),
        selectinload(Transaction.actions),
        selectinload(Transaction.audit_logs)
    ).where(Transaction.transaction_id == tx_id)

    res = await db.execute(stmt)
    tx = res.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # If no decision exists yet, analyze it on the fly
    if not tx.decisions:
        await agent_runner.analyze_and_decide(db, tx_id)
        # Reload
        res = await db.execute(stmt)
        tx = res.scalar_one_or_none()

    latest_dec = tx.decisions[-1] if tx.decisions else None
    
    # Parse feature breakdown
    feature_breakdown = []
    if latest_dec and latest_dec.feature_contributions_json:
        try:
            raw_breakdown = json.loads(latest_dec.feature_contributions_json)
            for item in raw_breakdown:
                feature_breakdown.append(FeatureWeight(
                    feature=item.get("feature", ""),
                    label=item.get("label", ""),
                    value=item.get("value", 0),
                    weight=item.get("weight", 0.0),
                    impact=item.get("impact", "NEUTRAL"),
                    explanation=item.get("explanation", ""),
                ))
        except Exception:
            pass

    decision_resp = None
    if latest_dec:
        decision_resp = RecoveryDecisionResponse(
            decision_id=latest_dec.decision_id,
            transaction_id=latest_dec.transaction_id,
            recovery_probability=latest_dec.recovery_probability,
            churn_probability=latest_dec.churn_probability,
            recommended_strategy=latest_dec.recommended_strategy,
            reason_summary=latest_dec.reason_summary,
            feature_contributions_json=latest_dec.feature_contributions_json,
            confidence_score=latest_dec.confidence_score,
            policy_status=latest_dec.policy_status,
            policy_rule_triggered=latest_dec.policy_rule_triggered,
            created_at=latest_dec.created_at,
            feature_breakdown=feature_breakdown,
        )

    # Recovery Priority
    rec_prob = latest_dec.recovery_probability if latest_dec else 0.5
    prio = calculate_recovery_priority(rec_prob, tx.amount, tx.churn_probability)

    # Actions and Audits sorted chronologically
    actions_resp = [
        RecoveryActionResponse(
            action_id=a.action_id,
            decision_id=a.decision_id,
            transaction_id=a.transaction_id,
            action_type=a.action_type,
            status=a.status,
            channel=a.channel,
            payload_json=a.payload_json,
            approval_status=a.approval_status,
            approved_by=a.approved_by,
            approved_at=a.approved_at,
            executed_at=a.executed_at,
            simulation_outcome=a.simulation_outcome,
            outcome_recovered_amount=a.outcome_recovered_amount,
        )
        for a in sorted(tx.actions, key=lambda x: x.action_id, reverse=True)
    ]

    audit_resp = [
        AuditLogResponse(
            log_id=log.log_id,
            transaction_id=log.transaction_id,
            action_id=log.action_id,
            actor=log.actor,
            event_type=log.event_type,
            message=log.message,
            metadata_json=log.metadata_json,
            timestamp=log.timestamp,
        )
        for log in sorted(tx.audit_logs, key=lambda x: x.timestamp)
    ]

    cust_resp = None
    if tx.customer:
        cust_resp = CustomerResponse(
            customer_id=tx.customer.customer_id,
            name=tx.customer.name,
            email=tx.customer.email,
            phone=tx.customer.phone,
            clv=tx.customer.clv,
            segment=tx.customer.segment,
            subscription_age_months=tx.customer.subscription_age_months,
            avg_payment_hour=tx.customer.avg_payment_hour,
            opted_out=tx.customer.opted_out,
            created_at=tx.customer.created_at,
        )

    return TransactionDetailResponse(
        transaction_id=tx.transaction_id,
        customer_id=tx.customer_id,
        amount=tx.amount,
        currency=tx.currency,
        timestamp=tx.timestamp,
        payment_method=tx.payment_method,
        failure_reason=tx.failure_reason,
        retry_count=tx.retry_count,
        status=tx.status,
        recovered_amount=tx.recovered_amount,
        recovered_at=tx.recovered_at,
        prev_payment_success_rate=tx.prev_payment_success_rate,
        prev_recovery_success_rate=tx.prev_recovery_success_rate,
        churn_probability=tx.churn_probability,
        customer=cust_resp,
        latest_decision=decision_resp,
        actions=actions_resp,
        audit_logs=audit_resp,
        recovery_priority=prio,
    )


@router.post("/{tx_id}/analyze")
async def analyze_transaction(tx_id: str, db: AsyncSession = Depends(get_db)):
    """Triggers immediate re-analysis and strategy recommendation."""
    result = await agent_runner.analyze_and_decide(db, tx_id)
    return result
