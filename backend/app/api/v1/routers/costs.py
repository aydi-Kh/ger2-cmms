"""
GER2 CMMS — Cost Management Router
Endpoints: cost records, TCO calculation, budget variance.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import require_roles, Role
from app.models.cost import CostRecord

router = APIRouter(prefix="/costs", tags=["Cost Management"])


@router.get("/records", response_model=List[dict])
async def list_cost_records(
    asset_id: Optional[str] = Query(None),
    center_id: Optional[str] = Query(None),
    period_month: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    stmt = select(CostRecord)
    if asset_id:    stmt = stmt.where(CostRecord.asset_id == asset_id)
    if center_id:   stmt = stmt.where(CostRecord.center_id == center_id)
    if period_month: stmt = stmt.where(CostRecord.period_month == period_month)
    stmt = stmt.order_by(CostRecord.created_at.desc()).limit(200)
    result = await db.execute(stmt)
    return [
        {"id": r.id, "asset_id": r.asset_id, "center_id": r.center_id,
         "cost_type": r.cost_type, "amount": r.amount, "period_month": r.period_month}
        for r in result.scalars().all()
    ]


@router.get("/tco/{asset_id}", summary="Calculate Total Cost of Ownership for an asset")
async def get_tco(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    result = await db.execute(
        select(func.sum(CostRecord.amount)).where(CostRecord.asset_id == asset_id)
    )
    total_maint = result.scalar() or 0.0
    asset = await db.get(__import__("app.models.asset", fromlist=["Asset"]).Asset, asset_id)
    acquisition = asset.acquisition_cost or 0.0 if asset else 0.0
    return {
        "asset_id": asset_id,
        "acquisition_cost": acquisition,
        "cumulative_maintenance": total_maint,
        "total_tco": acquisition + total_maint,
    }


@router.get("/dashboard/summary", summary="Aggregated cost KPIs for dashboard")
async def cost_summary(
    center_id: Optional[str] = Query(None),
    period_month: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    stmt = select(CostRecord.cost_type, func.sum(CostRecord.amount).label("total"))
    if center_id: stmt = stmt.where(CostRecord.center_id == center_id)
    if period_month: stmt = stmt.where(CostRecord.period_month == period_month)
    stmt = stmt.group_by(CostRecord.cost_type)
    result = await db.execute(stmt)
    rows = result.all()
    breakdown = {r.cost_type: float(r.total) for r in rows}
    grand_total = sum(breakdown.values())
    return {"total": grand_total, "breakdown": breakdown, "period": period_month}
