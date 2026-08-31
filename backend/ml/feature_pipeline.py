"""
Feature extraction, transformations, and interpretability utilities for REVIVE.
"""
import numpy as np
from typing import Dict, Any, List, Tuple
from backend.ml.dataset_generator import FAILURE_REASONS

FEATURE_NAMES = [
    "failure_is_insufficient_funds",
    "failure_is_network_timeout",
    "failure_is_auth_failure",
    "failure_is_card_expired",
    "failure_is_bank_declined",
    "failure_is_limit_exceeded",
    "failure_is_abandoned",
    "failure_is_unknown",
    "log_amount",
    "prev_payment_success_rate",
    "prev_recovery_success_rate",
    "retry_count",
    "churn_probability",
    "time_affinity_score",
]

FEATURE_LABELS = {
    "failure_is_insufficient_funds": "Failure: Insufficient Funds",
    "failure_is_network_timeout": "Failure: Network Timeout",
    "failure_is_auth_failure": "Failure: Auth / OTP Drop",
    "failure_is_card_expired": "Failure: Card Expired",
    "failure_is_bank_declined": "Failure: Bank Declined",
    "failure_is_limit_exceeded": "Failure: Limit Exceeded",
    "failure_is_abandoned": "Failure: Payment Abandoned",
    "failure_is_unknown": "Failure: Unknown Reason",
    "log_amount": "Transaction Value (Normalized)",
    "prev_payment_success_rate": "Past Payment Success Rate",
    "prev_recovery_success_rate": "Historical Recovery Success Rate",
    "retry_count": "Exhausted Retries",
    "churn_probability": "Customer Churn Risk",
    "time_affinity_score": "Historical Peak Hour Match",
}


def extract_features(tx_data: Dict[str, Any], customer_data: Dict[str, Any] = None) -> np.ndarray:
    """
    Extracts numerical feature vector for a single transaction.
    """
    failure_reason = tx_data.get("failure_reason", "UNKNOWN")
    amount = float(tx_data.get("amount", 1000.0))
    prev_pay_rate = float(tx_data.get("prev_payment_success_rate", 0.85))
    prev_rec_rate = float(tx_data.get("prev_recovery_success_rate", 0.50))
    retry_count = int(tx_data.get("retry_count", 0))
    churn_prob = float(tx_data.get("churn_probability", 0.15))

    # Time affinity match
    time_affinity = 0.5
    tx_time = tx_data.get("timestamp")
    if customer_data and tx_time:
        if isinstance(tx_time, str):
            from datetime import datetime
            try:
                tx_time = datetime.fromisoformat(tx_time)
            except Exception:
                tx_time = None
        if hasattr(tx_time, "hour"):
            avg_hour = customer_data.get("avg_payment_hour", 18)
            hour_diff = abs(tx_time.hour - avg_hour)
            time_affinity = max(0.1, 1.0 - (hour_diff / 12.0))

    features = [
        1.0 if failure_reason == "INSUFFICIENT_FUNDS" else 0.0,
        1.0 if failure_reason == "NETWORK_TIMEOUT" else 0.0,
        1.0 if failure_reason == "AUTHENTICATION_FAILURE" else 0.0,
        1.0 if failure_reason == "CARD_EXPIRED" else 0.0,
        1.0 if failure_reason == "BANK_DECLINED" else 0.0,
        1.0 if failure_reason == "LIMIT_EXCEEDED" else 0.0,
        1.0 if failure_reason == "PAYMENT_ABANDONED" else 0.0,
        1.0 if failure_reason == "UNKNOWN" else 0.0,
        np.log1p(max(1.0, amount)) / 10.0,  # normalized log amount
        prev_pay_rate,
        prev_rec_rate,
        retry_count / 5.0,  # normalized retry count
        churn_prob,
        time_affinity,
    ]
    return np.array(features, dtype=np.float32)


def generate_feature_explanations(
    features: np.ndarray,
    coefficients: np.ndarray,
    intercept: float
) -> List[Dict[str, Any]]:
    """
    Computes waterfall contributions of each feature to log-odds.
    """
    contributions = features * coefficients
    breakdown = []

    for i, (name, label) in enumerate(FEATURE_LABELS.items()):
        val = features[i]
        weight = float(contributions[i])
        
        # Skip zero one-hot indicators
        if "failure_is" in name and val == 0.0:
            continue
            
        impact = "POSITIVE" if weight > 0.05 else ("NEGATIVE" if weight < -0.05 else "NEUTRAL")
        
        if name == "prev_payment_success_rate":
            explanation = f"Customer has a {val*100:.0f}% historical payment reliability rate"
        elif name == "retry_count":
            explanation = f"{int(val*5)} retries already attempted (diminishing probability)"
        elif name == "churn_probability":
            explanation = f"{val*100:.0f}% churn risk assessed from recent activity"
        elif name == "time_affinity_score":
            explanation = f"Failure occurred within active customer payment window ({val*100:.0f}% match)"
        elif "failure_is" in name:
            explanation = f"Payment failure category: {name.replace('failure_is_', '').replace('_', ' ').title()}"
        elif name == "log_amount":
            explanation = f"Transaction amount normalized factor ({weight:+.2f} log-odds)"
        else:
            explanation = f"{label} impact on recovery probability"

        breakdown.append({
            "feature": name,
            "label": label,
            "value": round(float(val), 2),
            "weight": round(weight, 3),
            "impact": impact,
            "explanation": explanation,
        })

    # Sort by absolute weight contribution
    breakdown.sort(key=lambda x: abs(x["weight"]), reverse=True)
    return breakdown
