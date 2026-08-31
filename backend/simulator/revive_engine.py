"""
REVIVE Autonomous Agent Simulator Engine.
Simulates context-aware, strategy-routed, guardrail-governed recovery across synthetic records.
"""
from typing import List, Dict, Any


def run_revive_simulation(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
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
        prev_rate = tx.get("prev_payment_success_rate", 0.85)
        prev_rec = tx.get("prev_recovery_success_rate", 0.55)
        retry_count = tx.get("retry_count", 0)
        is_high_val = amount >= 10000.0

        if is_high_val:
            high_val_tx_count += 1

        if reason not in category_stats:
            category_stats[reason] = {"total": 0, "recovered": 0, "val_total": 0.0, "val_rec": 0.0}
        category_stats[reason]["total"] += 1
        category_stats[reason]["val_total"] += amount

        # REVIVE Strategy Selection & Efficiency:
        # 1. CARD_EXPIRED: 0 retries used. Sends Payment Update Link -> ~72% recovery
        # 2. NETWORK_TIMEOUT: 1 intelligent retry at optimal hour -> ~88% recovery
        # 3. AUTHENTICATION_FAILURE: 1-click retry nudge -> ~76% recovery
        # 4. INSUFFICIENT_FUNDS: Scheduled retry at optimal time + nudge -> ~62% recovery
        # 5. BANK_DECLINED: Escalation if high-value (~68%), else delayed retry (~45%)
        # 6. STOP_RECOVERY on exhausted cards (0 extra retries spent)

        retries_spent = 0
        revive_success_prob = 0.0

        if reason == "CARD_EXPIRED":
            retries_spent = 0  # Policy prevents blind retries
            revive_success_prob = 0.72 * (0.5 + 0.5 * prev_rec)
        elif reason == "NETWORK_TIMEOUT":
            retries_spent = 1
            revive_success_prob = 0.88 * prev_rate
        elif reason == "AUTHENTICATION_FAILURE":
            retries_spent = 1
            revive_success_prob = 0.76 * prev_rate
        elif reason == "INSUFFICIENT_FUNDS":
            retries_spent = 1
            revive_success_prob = 0.64 * (0.6 * prev_rate + 0.4 * prev_rec)
        elif reason == "BANK_DECLINED":
            retries_spent = 1 if not is_high_val else 0
            revive_success_prob = 0.68 if is_high_val else 0.46 * prev_rate
        elif reason == "LIMIT_EXCEEDED":
            retries_spent = 0
            revive_success_prob = 0.55 if is_high_val else 0.38
        elif reason == "PAYMENT_ABANDONED":
            retries_spent = 0
            revive_success_prob = 0.65 * (0.5 + 0.5 * prev_rec)
        else:
            retries_spent = 1
            revive_success_prob = 0.35 * prev_rate

        # Guardrail cost cap if already failed many times
        if retry_count >= 3:
            retries_spent = 0
            revive_success_prob *= 0.3

        total_retries_attempted += retries_spent

        # Deterministic simulation hash
        hash_val = (abs(hash(tx["transaction_id"])) % 10000) / 10000.0
        success = hash_val < revive_success_prob

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
