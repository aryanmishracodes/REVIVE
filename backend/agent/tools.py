"""
The 10 real backend agent tools used by REVIVE's autonomous decision and execution system.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Customer, Transaction, RecoveryDecision, RecoveryAction, AuditLog
from backend.ml.recovery_model import ml_model


async def get_transaction(db: AsyncSession, tx_id: str) -> Optional[Dict[str, Any]]:
    """Tool 1: Fetches transaction details and current recovery status."""
    stmt = select(Transaction).where(Transaction.transaction_id == tx_id)
    res = await db.execute(stmt)
    tx = res.scalar_one_or_none()
    if not tx:
        return None
    return {
        "transaction_id": tx.transaction_id,
        "customer_id": tx.customer_id,
        "amount": tx.amount,
        "currency": tx.currency,
        "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
        "payment_method": tx.payment_method,
        "failure_reason": tx.failure_reason,
        "retry_count": tx.retry_count,
        "status": tx.status,
        "recovered_amount": tx.recovered_amount,
        "prev_payment_success_rate": tx.prev_payment_success_rate,
        "prev_recovery_success_rate": tx.prev_recovery_success_rate,
        "churn_probability": tx.churn_probability,
    }


async def get_customer(db: AsyncSession, customer_id: str) -> Optional[Dict[str, Any]]:
    """Tool 2: Fetches customer profile, CLV, tenure, segment, and preferences."""
    stmt = select(Customer).where(Customer.customer_id == customer_id)
    res = await db.execute(stmt)
    cust = res.scalar_one_or_none()
    if not cust:
        return None
    return {
        "customer_id": cust.customer_id,
        "name": cust.name,
        "email": cust.email,
        "phone": cust.phone,
        "clv": cust.clv,
        "segment": cust.segment,
        "subscription_age_months": cust.subscription_age_months,
        "avg_payment_hour": cust.avg_payment_hour,
        "opted_out": cust.opted_out,
    }


async def get_payment_history(db: AsyncSession, customer_id: str) -> List[Dict[str, Any]]:
    """Tool 3: Fetches recent payment history for a customer."""
    stmt = select(Transaction).where(Transaction.customer_id == customer_id).order_by(Transaction.timestamp.desc()).limit(10)
    res = await db.execute(stmt)
    txs = res.scalars().all()
    return [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            "status": t.status,
            "failure_reason": t.failure_reason,
            "retry_count": t.retry_count,
        }
        for t in txs
    ]


async def predict_recovery_probability(db: AsyncSession, tx_id: str) -> Dict[str, Any]:
    """Tool 4: Runs Logistic Regression ML scoring with waterfall explainability."""
    tx_data = await get_transaction(db, tx_id)
    if not tx_data:
        raise ValueError(f"Transaction {tx_id} not found")
    cust_data = await get_customer(db, tx_data["customer_id"])
    
    prob, breakdown = ml_model.predict_probability(tx_data, cust_data)
    return {
        "transaction_id": tx_id,
        "recovery_probability": prob,
        "confidence_score": 0.88,
        "feature_breakdown": breakdown,
    }


def calculate_recovery_priority(recovery_prob: float, amount: float, churn_prob: float) -> str:
    """Tool 5: Computes operational priority tier (P0 = Critical / High Value to P3 = Low)."""
    expected_value = amount * recovery_prob
    if amount >= 10000.0 or expected_value >= 7500.0:
        return "P0"
    elif expected_value >= 2500.0 or churn_prob > 0.50:
        return "P1"
    elif expected_value >= 800.0:
        return "P2"
    else:
        return "P3"


async def schedule_retry(db: AsyncSession, tx_id: str, optimal_time: Optional[datetime] = None) -> Dict[str, Any]:
    """Tool 6: Schedules an intelligent retry at customer's optimal payment hour."""
    tx = await get_transaction(db, tx_id)
    if not tx:
        raise ValueError(f"Transaction {tx_id} not found")
    
    if not optimal_time:
        cust = await get_customer(db, tx["customer_id"])
        target_hour = cust.get("avg_payment_hour", 18) if cust else 18
        now = datetime.utcnow()
        optimal_time = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if optimal_time <= now:
            optimal_time += timedelta(days=1)

    return {
        "action_type": "INTELLIGENT_RETRY",
        "transaction_id": tx_id,
        "scheduled_time": optimal_time.isoformat(),
        "channel": "PAYMENT_GATEWAY",
        "description": f"Retry scheduled for optimal customer success window: {optimal_time.strftime('%I:%M %p')}",
    }


async def generate_customer_nudge(db: AsyncSession, tx_id: str, channel: str = "EMAIL", tone: str = "HELPFUL") -> Dict[str, Any]:
    """Tool 7: Synthesizes a contextual, personalized payment recovery message."""
    tx = await get_transaction(db, tx_id)
    cust = await get_customer(db, tx["customer_id"]) if tx else None
    
    cust_name = cust["name"] if cust else "Valued Customer"
    amount = tx["amount"] if tx else 0.0
    reason = tx.get("failure_reason", "UNKNOWN") if tx else "UNKNOWN"

    if reason == "CARD_EXPIRED":
        subject = "Action Required: Update your payment method"
        body = (f"Hi {cust_name}, your recent payment of ₹{amount:,.2f} could not be processed because your card on file has expired. "
                f"Please update your card details using the secure link below to maintain uninterrupted service.")
    elif reason == "INSUFFICIENT_FUNDS":
        subject = "Payment reminder for your subscription"
        body = (f"Hi {cust_name}, we noticed your recent payment of ₹{amount:,.2f} didn't go through. "
                f"You can quickly complete your payment with 1-click UPI or card using the link below.")
    elif reason in ["NETWORK_TIMEOUT", "AUTHENTICATION_FAILURE"]:
        subject = "Quick update on your recent payment"
        body = (f"Hi {cust_name}, your payment of ₹{amount:,.2f} experienced a momentary network interruption. "
                f"Tap here to retry instantly without re-entering your payment details.")
    else:
        subject = "Important notice regarding your payment"
        body = (f"Hi {cust_name}, your transaction of ₹{amount:,.2f} requires attention. "
                f"Please review your payment method to complete this order.")

    return {
        "action_type": "CUSTOMER_NUDGE",
        "channel": channel,
        "subject": subject,
        "body": body,
        "recipient": cust["email"] if (cust and channel == "EMAIL") else (cust.get("phone") if cust else "customer"),
    }


async def send_notification(recipient: str, channel: str, template_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Tool 8: Dispatches simulated notification through configured channel."""
    return {
        "status": "SENT",
        "recipient": recipient,
        "channel": channel,
        "timestamp": datetime.utcnow().isoformat(),
        "delivery_id": f"DELIV-{datetime.utcnow().strftime('%H%M%S%f')[:10]}",
    }


async def create_escalation(db: AsyncSession, tx_id: str, reason: str, urgency: str = "HIGH") -> Dict[str, Any]:
    """Tool 9: Creates an escalation case for merchant accounts/ops team."""
    tx = await get_transaction(db, tx_id)
    amount = tx["amount"] if tx else 0.0
    return {
        "action_type": "ESCALATION",
        "ticket_id": f"ESC-{datetime.utcnow().strftime('%M%S')}-{tx_id[-4:]}",
        "transaction_id": tx_id,
        "urgency": urgency,
        "amount": amount,
        "reason": reason,
        "assigned_team": "FINANCE_OPS_TEAM",
        "created_at": datetime.utcnow().isoformat(),
    }


async def record_outcome(
    db: AsyncSession,
    action_id: str,
    outcome: str,
    recovered_amount: float
) -> Dict[str, Any]:
    """Tool 10: Records execution results and updates audit/transaction status."""
    stmt = select(RecoveryAction).where(RecoveryAction.action_id == action_id)
    res = await db.execute(stmt)
    action = res.scalar_one_or_none()
    if action:
        action.status = "EXECUTED"
        action.simulation_outcome = outcome
        action.outcome_recovered_amount = recovered_amount
        action.executed_at = datetime.utcnow()
        
        # Update transaction if recovered
        if outcome == "SUCCESS" and recovered_amount > 0:
            tx_stmt = select(Transaction).where(Transaction.transaction_id == action.transaction_id)
            tx_res = await db.execute(tx_stmt)
            tx = tx_res.scalar_one_or_none()
            if tx:
                tx.status = "RECOVERED"
                tx.recovered_amount = recovered_amount
                tx.recovered_at = datetime.utcnow()
        await db.commit()

    return {
        "action_id": action_id,
        "outcome": outcome,
        "recovered_amount": recovered_amount,
        "recorded_at": datetime.utcnow().isoformat(),
    }
