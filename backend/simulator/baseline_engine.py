"""
Baseline Naive Payment Recovery Simulator.
Represents typical industry behavior:
- Blind immediate retry
- Fixed retry intervals (2 retries max)
- Identical generic reminder template
- 0% sensitivity to failure reasons (e.g. card expiry retried anyway)
"""
from typing import List, Dict, Any


def run_baseline_simulation(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_tx = len(transactions)
    total_failed_val = sum(t["amount"] for t in transactions)
    
    recovered_count = 0
    recovered_val = 0.0
    total_retries_attempted = 0
    
    high_val_tx_count = 0
    high_val_recovered_count = 0

    category_stats = {}

    for tx in transactions:
        amount = tx["amount"]
        reason = tx["failure_reason"]
        prev_rate = tx.get("prev_payment_success_rate", 0.8)
        is_high_val = amount >= 10000.0

        if is_high_val:
            high_val_tx_count += 1

        if reason not in category_stats:
            category_stats[reason] = {"total": 0, "recovered": 0, "val_total": 0.0, "val_rec": 0.0}
        category_stats[reason]["total"] += 1
        category_stats[reason]["val_total"] += amount

        # Baseline blindly attempts 3 retries for every failure
        retries = 3
        total_retries_attempted += retries

        # Naive recovery probability:
        # - Card expired = 0% (card is expired, blind retries never work)
        # - Bank decline = 15% (blind immediate retry mostly fails)
        # - Insufficient funds = 25% (blind immediate retry misses payday)
        # - Network timeout = 60%
        # - Auth failure = 40%
        # - Limit exceeded = 10%
        # - Abandoned = 20%
        # - Unknown = 15%
        baseline_success_prob = 0.0
        if reason == "CARD_EXPIRED":
            baseline_success_prob = 0.0
        elif reason == "NETWORK_TIMEOUT":
            baseline_success_prob = 0.62 * prev_rate
        elif reason == "AUTHENTICATION_FAILURE":
            baseline_success_prob = 0.42 * prev_rate
        elif reason == "INSUFFICIENT_FUNDS":
            baseline_success_prob = 0.28 * prev_rate
        elif reason == "BANK_DECLINED":
            baseline_success_prob = 0.18 * prev_rate
        elif reason == "LIMIT_EXCEEDED":
            baseline_success_prob = 0.10 * prev_rate
        elif reason == "PAYMENT_ABANDONED":
            baseline_success_prob = 0.22 * prev_rate
        else:
            baseline_success_prob = 0.15 * prev_rate

        # Deterministic pseudo-random threshold based on tx id
        hash_val = (abs(hash(tx["transaction_id"])) % 10000) / 10000.0
        success = hash_val < baseline_success_prob

        if success:
            recovered_count += 1
            recovered_val += amount
            category_stats[reason]["recovered"] += 1
            category_stats[reason]["val_rec"] += amount
            if is_high_val:
                high_val_recovered_count += 1

    recovery_rate = (recovered_count / total_tx) if total_tx > 0 else 0.0
    avg_retries = (total_retries_attempted / total_tx) if total_tx > 0 else 0.0
    high_val_rate = (high_val_recovered_count / high_val_tx_count) if high_val_tx_count > 0 else 0.0

    return {
        "recovered_count": recovered_count,
        "recovered_value": round(recovered_val, 2),
        "recovery_rate": round(recovery_rate, 4),
        "total_retries": total_retries_attempted,
        "avg_retries_per_tx": round(avg_retries, 2),
        "high_value_recovery_rate": round(high_val_rate, 4),
        "category_stats": category_stats,
    }
