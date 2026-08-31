"""
Benchmark Comparator: Baseline vs. REVIVE.
Executes both models across the synthetic database and computes uplift statistics.
"""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.models import Transaction, SimulationRun
from backend.simulator.baseline_engine import run_baseline_simulation
from backend.simulator.revive_engine import run_revive_simulation


async def run_full_benchmark(db: AsyncSession) -> Dict[str, Any]:
    # Fetch all transactions
    stmt = select(Transaction)
    res = await db.execute(stmt)
    tx_models = res.scalars().all()

    tx_list = [
        {
            "transaction_id": t.transaction_id,
            "amount": t.amount,
            "failure_reason": t.failure_reason,
            "retry_count": t.retry_count,
            "prev_payment_success_rate": t.prev_payment_success_rate,
            "prev_recovery_success_rate": t.prev_recovery_success_rate,
            "churn_probability": t.churn_probability,
        }
        for t in tx_models
    ]

    total_count = len(tx_list)
    baseline_res = run_baseline_simulation(tx_list)
    revive_res = run_revive_simulation(tx_list)

    # Compute Uplift
    base_val = baseline_res["recovered_value"]
    rev_val = revive_res["recovered_value"]
    uplift_val = round(rev_val - base_val, 2)
    uplift_pct = round(((rev_val - base_val) / base_val * 100.0), 2) if base_val > 0 else 0.0

    retries_saved_pct = round(
        ((baseline_res["total_retries"] - revive_res["total_retries"]) / baseline_res["total_retries"] * 100.0), 2
    ) if baseline_res["total_retries"] > 0 else 0.0

    # Category breakdown table
    categories = list(baseline_res["category_stats"].keys())
    breakdown_by_category = []
    for cat in categories:
        b_stat = baseline_res["category_stats"][cat]
        r_stat = revive_res["category_stats"][cat]
        b_rate = round((b_stat["recovered"] / b_stat["total"] * 100), 1) if b_stat["total"] > 0 else 0.0
        r_rate = round((r_stat["recovered"] / r_stat["total"] * 100), 1) if r_stat["total"] > 0 else 0.0
        breakdown_by_category.append({
            "category": cat,
            "total_count": b_stat["total"],
            "total_value": round(b_stat["val_total"], 2),
            "baseline_recovery_rate": b_rate,
            "revive_recovery_rate": r_rate,
            "baseline_recovered_value": round(b_stat["val_rec"], 2),
            "revive_recovered_value": round(r_stat["val_rec"], 2),
            "rate_uplift_pts": round(r_rate - b_rate, 1),
        })

    breakdown_by_category.sort(key=lambda x: x["rate_uplift_pts"], reverse=True)

    run_id = f"SIM-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()

    # Save to database
    sim_run = SimulationRun(
        run_id=run_id,
        timestamp=now,
        total_transactions=total_count,
        baseline_recovered_value=base_val,
        baseline_recovery_rate=baseline_res["recovery_rate"],
        revive_recovered_value=rev_val,
        revive_recovery_rate=revive_res["recovery_rate"],
        uplift_percentage=uplift_pct,
        avg_retries_baseline=baseline_res["avg_retries_per_tx"],
        avg_retries_revive=revive_res["avg_retries_per_tx"],
        high_value_baseline_recovery_rate=baseline_res["high_value_recovery_rate"],
        high_value_revive_recovery_rate=revive_res["high_value_recovery_rate"],
        metrics_json=json.dumps({
            "breakdown_by_category": breakdown_by_category,
            "retries_saved_percent": retries_saved_pct,
            "revenue_uplift_amount": uplift_val,
        }),
    )
    db.add(sim_run)
    await db.commit()

    return {
        "run_id": run_id,
        "timestamp": now.isoformat(),
        "total_transactions": total_count,
        "baseline_recovered_value": base_val,
        "baseline_recovery_rate": baseline_res["recovery_rate"],
        "baseline_avg_retries": baseline_res["avg_retries_per_tx"],
        "baseline_high_value_rate": baseline_res["high_value_recovery_rate"],
        "revive_recovered_value": rev_val,
        "revive_recovery_rate": revive_res["recovery_rate"],
        "revive_avg_retries": revive_res["avg_retries_per_tx"],
        "revive_high_value_rate": revive_res["high_value_recovery_rate"],
        "revenue_uplift_amount": uplift_val,
        "revenue_uplift_percent": uplift_pct,
        "retries_saved_percent": retries_saved_pct,
        "breakdown_by_category": breakdown_by_category,
    }
