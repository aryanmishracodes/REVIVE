"""
Dashboard API endpoints for Command Center.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.core.database import get_db
from backend.models import Transaction, RecoveryAction, RecoveryDecision, SimulationRun
from backend.schemas import MetricOverview, CategoryRecoveryStat

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=MetricOverview)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    # Total failed transactions and sum
    tx_stmt = select(
        func.count(Transaction.transaction_id).label("total_count"),
        func.sum(Transaction.amount).label("total_failed_val")
    )
    tx_res = await db.execute(tx_stmt)
    tx_row = tx_res.one()
    total_failed_count = tx_row.total_count or 0
    total_failed_val = float(tx_row.total_failed_val or 0.0)

    # Recovered
    rec_stmt = select(
        func.count(Transaction.transaction_id).label("rec_count"),
        func.sum(Transaction.recovered_amount).label("rec_val")
    ).where(Transaction.status == "RECOVERED")
    rec_res = await db.execute(rec_stmt)
    rec_row = rec_res.one()
    total_recovered_count = rec_row.rec_count or 0
    total_recovered_val = float(rec_row.rec_val or 0.0)

    # Latest Canonical Simulation Benchmark Run
    sim_stmt = select(SimulationRun).order_by(SimulationRun.timestamp.desc()).limit(1)
    sim_res = await db.execute(sim_stmt)
    latest_sim = sim_res.scalar_one_or_none()

    # Canonical recovery rate, recovered value & uplift from shared simulation benchmark
    if latest_sim:
        revive_uplift_pct = float(latest_sim.uplift_percentage)
        overall_recovery_rate = round(float(latest_sim.revive_recovery_rate) * 100, 1)
        recovered_val = round(float(latest_sim.revive_recovered_value), 2)
        recoverable_val = recovered_val  # Total Addressable Opportunity matches REVIVE ML predicted capture
        total_recovered_count = int(round(total_failed_count * float(latest_sim.revive_recovery_rate)))
    else:
        # Fallback to direct DB aggregation if simulation is absent
        dec_stmt = select(func.avg(RecoveryDecision.recovery_probability).label("avg_prob"))
        dec_res = await db.execute(dec_stmt)
        avg_prob = dec_res.scalar() or 0.48
        revive_uplift_pct = 0.0
        overall_recovery_rate = round((total_recovered_count / total_failed_count * 100), 1) if total_failed_count > 0 else 0.0
        recovered_val = round(total_recovered_val, 2)
        recoverable_val = round(total_failed_val * float(avg_prob), 2)

    # Pending approvals count
    act_stmt = select(func.count(RecoveryAction.action_id)).where(RecoveryAction.status == "PENDING_APPROVAL")
    act_res = await db.execute(act_stmt)
    pending_approvals = act_res.scalar() or 0

    # High-priority count (amount > 10k or high CLV)
    p0_stmt = select(func.count(Transaction.transaction_id)).where(Transaction.amount >= 10000.0)
    p0_res = await db.execute(p0_stmt)
    high_priority_count = p0_res.scalar() or 0

    return MetricOverview(
        total_failed_value=round(total_failed_val, 2),
        recoverable_value=recoverable_val,
        recovered_value=recovered_val,
        overall_recovery_rate=overall_recovery_rate,
        revive_uplift_percent=round(revive_uplift_pct, 2),
        high_priority_count=high_priority_count,
        pending_approvals_count=pending_approvals,
        total_failed_count=total_failed_count,
        total_recovered_count=total_recovered_count,
    )


@router.get("/distribution")
async def get_failure_distribution(db: AsyncSession = Depends(get_db)):
    import json
    sim_stmt = select(SimulationRun).order_by(SimulationRun.timestamp.desc()).limit(1)
    sim_res = await db.execute(sim_stmt)
    latest_sim = sim_res.scalar_one_or_none()

    if latest_sim and latest_sim.metrics_json:
        try:
            metrics_data = json.loads(latest_sim.metrics_json)
            breakdown = metrics_data.get("breakdown_by_category", [])
            if breakdown:
                dist = [
                    {
                        "failure_reason": item["category"],
                        "count": item["total_count"],
                        "failed_value": round(float(item["total_value"]), 2),
                        "recovered_value": round(float(item["revive_recovered_value"]), 2),
                        "recovery_rate": round(float(item["revive_recovery_rate"]), 1),
                        "baseline_recovered_value": round(float(item.get("baseline_recovered_value", 0.0)), 2),
                        "baseline_recovery_rate": round(float(item.get("baseline_recovery_rate", 0.0)), 1),
                        "rate_uplift_pts": round(float(item.get("rate_uplift_pts", 0.0)), 1),
                    }
                    for item in breakdown
                ]
                dist.sort(key=lambda x: x["count"], reverse=True)
                return dist
        except Exception:
            pass

    stmt = select(
        Transaction.failure_reason,
        func.count(Transaction.transaction_id).label("count"),
        func.sum(Transaction.amount).label("failed_value"),
        func.sum(Transaction.recovered_amount).label("recovered_value")
    ).group_by(Transaction.failure_reason)
    res = await db.execute(stmt)
    rows = res.all()

    distribution = []
    for r in rows:
        count = r.count
        f_val = float(r.failed_value or 0.0)
        r_val = float(r.recovered_value or 0.0)
        rec_rate = round((r_val / f_val * 100), 1) if f_val > 0 else 0.0
        distribution.append({
            "failure_reason": r.failure_reason,
            "count": count,
            "failed_value": round(f_val, 2),
            "recovered_value": round(r_val, 2),
            "recovery_rate": rec_rate,
        })
    distribution.sort(key=lambda x: x["count"], reverse=True)
    return distribution
