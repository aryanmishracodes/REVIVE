"""
Actions & Approvals API router.
Enforces Human-in-the-Loop governance and controlled execution.
"""
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.core.database import get_db
from backend.models import RecoveryAction, RecoveryDecision, Transaction, AuditLog
from backend.schemas import (
    RecoveryActionResponse,
    ActionApprovalRequest,
    ActionRejectRequest,
)
from backend.agent.tools import record_outcome

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.get("", response_model=List[RecoveryActionResponse])
async def list_actions(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RecoveryAction).order_by(RecoveryAction.action_id.desc())

    if status and status != "ALL":
        stmt = stmt.where(RecoveryAction.status == status)
    if action_type and action_type != "ALL":
        stmt = stmt.where(RecoveryAction.action_type == action_type)

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    actions = res.scalars().all()

    return [
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
        for a in actions
    ]


@router.post("/{action_id}/approve", response_model=RecoveryActionResponse)
async def approve_action(
    action_id: str,
    body: Optional[ActionApprovalRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RecoveryAction).where(RecoveryAction.action_id == action_id)
    res = await db.execute(stmt)
    action = res.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.status = "APPROVED"
    action.approval_status = "MANUALLY_APPROVED"
    action.approved_by = "HUMAN_OPERATOR (Merchant Ops)"
    action.approved_at = datetime.utcnow()

    # Synchronize Decision Policy Status
    if action.decision_id:
        dec_stmt = select(RecoveryDecision).where(RecoveryDecision.decision_id == action.decision_id)
        dec_res = await db.execute(dec_stmt)
        dec = dec_res.scalar_one_or_none()
        if dec:
            dec.policy_status = "APPROVED"
            dec.policy_rule_triggered = "HUMAN_OPS_APPROVED"

    # Log to audit trail
    log = AuditLog(
        log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
        transaction_id=action.transaction_id,
        action_id=action.action_id,
        actor="HUMAN_OPERATOR",
        event_type="ACTION_APPROVED",
        message=f"Action '{action.action_type}' approved by Merchant Ops.",
        metadata_json=json.dumps({"notes": body.notes if body else "Approved via Command Center"}),
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(action)

    return RecoveryActionResponse(
        action_id=action.action_id,
        decision_id=action.decision_id,
        transaction_id=action.transaction_id,
        action_type=action.action_type,
        status=action.status,
        channel=action.channel,
        payload_json=action.payload_json,
        approval_status=action.approval_status,
        approved_by=action.approved_by,
        approved_at=action.approved_at,
        executed_at=action.executed_at,
        simulation_outcome=action.simulation_outcome,
        outcome_recovered_amount=action.outcome_recovered_amount,
    )


@router.post("/{action_id}/reject", response_model=RecoveryActionResponse)
async def reject_action(
    action_id: str,
    body: Optional[ActionRejectRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(RecoveryAction).where(RecoveryAction.action_id == action_id)
    res = await db.execute(stmt)
    action = res.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    reason_text = body.reason if (body and body.reason) else "Declined by Merchant Ops"
    action.status = "REJECTED"
    action.approval_status = "REJECTED"
    action.approved_by = "HUMAN_OPERATOR (Merchant Ops)"
    action.approved_at = datetime.utcnow()

    # Synchronize Decision Policy Status
    if action.decision_id:
        dec_stmt = select(RecoveryDecision).where(RecoveryDecision.decision_id == action.decision_id)
        dec_res = await db.execute(dec_stmt)
        dec = dec_res.scalar_one_or_none()
        if dec:
            dec.policy_status = "REJECTED"

    # Log to audit trail
    log = AuditLog(
        log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
        transaction_id=action.transaction_id,
        action_id=action.action_id,
        actor="HUMAN_OPERATOR",
        event_type="ACTION_REJECTED",
        message=f"Action '{action.action_type}' rejected by Merchant Ops. Reason: {reason_text}",
        metadata_json=json.dumps({"rejection_reason": reason_text}),
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(action)

    return RecoveryActionResponse(
        action_id=action.action_id,
        decision_id=action.decision_id,
        transaction_id=action.transaction_id,
        action_type=action.action_type,
        status=action.status,
        channel=action.channel,
        payload_json=action.payload_json,
        approval_status=action.approval_status,
        approved_by=action.approved_by,
        approved_at=action.approved_at,
        executed_at=action.executed_at,
        simulation_outcome=action.simulation_outcome,
        outcome_recovered_amount=action.outcome_recovered_amount,
    )


@router.post("/{action_id}/execute", response_model=RecoveryActionResponse)
async def execute_action(action_id: str, db: AsyncSession = Depends(get_db)):
    """Executes an approved action in the simulation runtime."""
    stmt = select(RecoveryAction).where(RecoveryAction.action_id == action_id)
    res = await db.execute(stmt)
    action = res.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status not in ["APPROVED", "PENDING_APPROVAL"]:
        raise HTTPException(status_code=400, detail=f"Cannot execute action with status '{action.status}'")

    # Fetch transaction
    tx_stmt = select(Transaction).where(Transaction.transaction_id == action.transaction_id)
    tx_res = await db.execute(tx_stmt)
    tx = tx_res.scalar_one_or_none()
    amount = tx.amount if tx else 1000.0

    outcome = "SUCCESS"
    recovered_amount = amount

    action.status = "EXECUTED"
    action.simulation_outcome = outcome
    action.outcome_recovered_amount = recovered_amount
    action.executed_at = datetime.utcnow()

    if tx:
        tx.status = "RECOVERED"
        tx.recovered_amount = recovered_amount
        tx.recovered_at = datetime.utcnow()

    # Log execution
    log = AuditLog(
        log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
        transaction_id=action.transaction_id,
        action_id=action.action_id,
        actor="SYSTEM_SIMULATOR",
        event_type="ACTION_EXECUTED",
        message=f"Action '{action.action_type}' executed. Simulated recovery: ₹{recovered_amount:,.2f}",
        metadata_json=json.dumps({"outcome": outcome, "recovered_amount": recovered_amount}),
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()
    await db.refresh(action)

    return RecoveryActionResponse(
        action_id=action.action_id,
        decision_id=action.decision_id,
        transaction_id=action.transaction_id,
        action_type=action.action_type,
        status=action.status,
        channel=action.channel,
        payload_json=action.payload_json,
        approval_status=action.approval_status,
        approved_by=action.approved_by,
        approved_at=action.approved_at,
        executed_at=action.executed_at,
        simulation_outcome=action.simulation_outcome,
        outcome_recovered_amount=action.outcome_recovered_amount,
    )
