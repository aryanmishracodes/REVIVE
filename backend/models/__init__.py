"""
SQLAlchemy models for Customers, Transactions, Decisions, Actions, AuditLogs, SimulationRuns.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    clv = Column(Float, default=0.0)
    segment = Column(String(32), default="SMB")  # Enterprise, Growth, SMB, Consumer
    subscription_age_months = Column(Integer, default=1)
    avg_payment_hour = Column(Integer, default=18)  # 0-23 hour in customer time
    opted_out = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="customer")


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    payment_method = Column(String(32), default="UPI")  # UPI, CARD, NETBANKING, WALLET
    failure_reason = Column(String(64), nullable=False, index=True)
    retry_count = Column(Integer, default=0)
    status = Column(String(32), default="FAILED", index=True)  # FAILED, PENDING_RECOVERY, RECOVERED, ESCALATED, STOPPED
    recovered_amount = Column(Float, default=0.0)
    recovered_at = Column(DateTime, nullable=True)
    
    # Historical / Context Features
    prev_payment_success_rate = Column(Float, default=0.85)
    prev_recovery_success_rate = Column(Float, default=0.50)
    churn_probability = Column(Float, default=0.15)
    
    # Relationships
    customer = relationship("Customer", back_populates="transactions")
    decisions = relationship("RecoveryDecision", back_populates="transaction", cascade="all, delete-orphan")
    actions = relationship("RecoveryAction", back_populates="transaction", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="transaction", cascade="all, delete-orphan")


class RecoveryDecision(Base):
    __tablename__ = "recovery_decisions"

    decision_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    recovery_probability = Column(Float, nullable=False)
    churn_probability = Column(Float, nullable=False)
    recommended_strategy = Column(String(64), nullable=False)  # INTELLIGENT_RETRY, CUSTOMER_NUDGE, PAYMENT_UPDATE, ESCALATION, STOP_RECOVERY
    reason_summary = Column(Text, nullable=False)
    feature_contributions_json = Column(Text, default="{}")  # JSON string of positive/negative weights
    confidence_score = Column(Float, default=0.85)
    policy_status = Column(String(32), default="APPROVED")  # APPROVED, REQUIRES_APPROVAL, BLOCKED
    policy_rule_triggered = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", back_populates="decisions")
    actions = relationship("RecoveryAction", back_populates="decision", cascade="all, delete-orphan")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    action_id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), ForeignKey("recovery_decisions.decision_id"), nullable=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # RETRY, NUDGE, PAYMENT_UPDATE, ESCALATION, STOP
    status = Column(String(32), default="PENDING_APPROVAL", index=True)  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, BLOCKED
    channel = Column(String(32), default="EMAIL")  # EMAIL, SMS, IN_APP
    payload_json = Column(Text, default="{}")  # e.g., message text, scheduled retry time
    approval_status = Column(String(32), default="AUTO_APPROVED")  # AUTO_APPROVED, PENDING_REVIEW, MANUALLY_APPROVED, REJECTED
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    simulation_outcome = Column(String(32), nullable=True)  # SUCCESS, FAILED, NO_OP
    outcome_recovered_amount = Column(Float, default=0.0)

    decision = relationship("RecoveryDecision", back_populates="actions")
    transaction = relationship("Transaction", back_populates="actions")
    audit_logs = relationship("AuditLog", back_populates="action", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    action_id = Column(String(64), ForeignKey("recovery_actions.action_id"), nullable=True)
    actor = Column(String(32), nullable=False)  # AI_AGENT, POLICY_ENGINE, HUMAN_OPERATOR, SYSTEM_SIMULATOR
    event_type = Column(String(64), nullable=False)  # FAILURE_DETECTED, ML_SCORED, STRATEGY_RECOMMENDED, POLICY_EVALUATED, ACTION_APPROVED, ACTION_EXECUTED, RECOVERY_RECORDED
    message = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    transaction = relationship("Transaction", back_populates="audit_logs")
    action = relationship("RecoveryAction", back_populates="audit_logs")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    run_id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_transactions = Column(Integer, default=0)
    baseline_recovered_value = Column(Float, default=0.0)
    baseline_recovery_rate = Column(Float, default=0.0)
    revive_recovered_value = Column(Float, default=0.0)
    revive_recovery_rate = Column(Float, default=0.0)
    uplift_percentage = Column(Float, default=0.0)
    avg_retries_baseline = Column(Float, default=0.0)
    avg_retries_revive = Column(Float, default=0.0)
    high_value_baseline_recovery_rate = Column(Float, default=0.0)
    high_value_revive_recovery_rate = Column(Float, default=0.0)
    metrics_json = Column(Text, default="{}")
