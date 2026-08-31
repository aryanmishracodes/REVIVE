"""
Pydantic Schemas for API requests and responses.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# --- Customer Schemas ---
class CustomerBase(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: Optional[str] = None
    clv: float = 0.0
    segment: str = "SMB"
    subscription_age_months: int = 1
    avg_payment_hour: int = 18
    opted_out: bool = False


class CustomerResponse(CustomerBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    log_id: str
    transaction_id: str
    action_id: Optional[str] = None
    actor: str
    event_type: str
    message: str
    metadata_json: Optional[str] = "{}"
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Decision Schemas ---
class FeatureWeight(BaseModel):
    feature: str
    label: str
    value: Any
    weight: float
    impact: str  # POSITIVE, NEGATIVE, NEUTRAL
    explanation: str


class RecoveryDecisionResponse(BaseModel):
    decision_id: str
    transaction_id: str
    recovery_probability: float
    churn_probability: float
    recommended_strategy: str
    reason_summary: str
    feature_contributions_json: Optional[str] = "{}"
    confidence_score: float
    policy_status: str
    policy_rule_triggered: Optional[str] = None
    created_at: datetime
    feature_breakdown: Optional[List[FeatureWeight]] = []
    model_config = ConfigDict(from_attributes=True)


# --- Action Schemas ---
class RecoveryActionResponse(BaseModel):
    action_id: str
    decision_id: Optional[str] = None
    transaction_id: str
    action_type: str
    status: str
    channel: str
    payload_json: Optional[str] = "{}"
    approval_status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    simulation_outcome: Optional[str] = None
    outcome_recovered_amount: float = 0.0
    model_config = ConfigDict(from_attributes=True)


class ActionApprovalRequest(BaseModel):
    notes: Optional[str] = None


class ActionRejectRequest(BaseModel):
    reason: str = Field(..., description="Reason for rejection")


# --- Transaction Schemas ---
class TransactionBase(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    timestamp: datetime
    payment_method: str
    failure_reason: str
    retry_count: int = 0
    status: str = "FAILED"
    recovered_amount: float = 0.0
    recovered_at: Optional[datetime] = None
    prev_payment_success_rate: float
    prev_recovery_success_rate: float
    churn_probability: float


class TransactionListResponse(TransactionBase):
    customer_name: Optional[str] = None
    customer_segment: Optional[str] = None
    recovery_probability: Optional[float] = None
    priority: Optional[str] = "P2"
    recommended_strategy: Optional[str] = None
    policy_status: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class TransactionDetailResponse(TransactionBase):
    customer: Optional[CustomerResponse] = None
    latest_decision: Optional[RecoveryDecisionResponse] = None
    actions: List[RecoveryActionResponse] = []
    audit_logs: List[AuditLogResponse] = []
    recovery_priority: str = "P1"
    model_config = ConfigDict(from_attributes=True)


# --- Dashboard Schemas ---
class MetricOverview(BaseModel):
    total_failed_value: float
    recoverable_value: float
    recovered_value: float
    overall_recovery_rate: float
    revive_uplift_percent: float
    high_priority_count: int
    pending_approvals_count: int
    total_failed_count: int
    total_recovered_count: int


class CategoryRecoveryStat(BaseModel):
    category: str
    total_count: int
    failed_value: float
    recovered_value: float
    recovery_rate: float
    top_strategy: str


# --- Simulator Schemas ---
class BenchmarkComparison(BaseModel):
    run_id: str
    timestamp: datetime
    total_transactions: int
    
    # Baseline
    baseline_recovered_value: float
    baseline_recovery_rate: float
    baseline_avg_retries: float
    baseline_high_value_rate: float
    
    # REVIVE
    revive_recovered_value: float
    revive_recovery_rate: float
    revive_avg_retries: float
    revive_high_value_rate: float
    
    # Uplift
    revenue_uplift_amount: float
    revenue_uplift_percent: float
    retries_saved_percent: float
    
    breakdown_by_category: List[Dict[str, Any]] = []
    sample_scenarios: List[Dict[str, Any]] = []
