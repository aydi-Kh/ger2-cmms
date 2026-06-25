"""
GER2 CMMS — Work Order API Router
Endpoints: CRUD, status transitions, cost accumulation, bulk operations.
"""
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import require_roles, Role
from app.core.cache import cache_invalidate_pattern
from app.models.workorder import WorkOrder, WOStatus
from app.schemas.workorder import WorkOrderCreate, WorkOrderUpdate, WorkOrderResponse
from app.integrations.kafka.producer import publish_event

router = APIRouter(prefix="/workorders", tags=["Work Orders"])

WO_VALID_TRANSITIONS = {
    WOStatus.BACKLOG:        [WOStatus.IN_PROGRESS, WOStatus.CANCELLED],
    WOStatus.IN_PROGRESS:    [WOStatus.PENDING_PARTS, WOStatus.COMPLETED, WOStatus.CANCELLED],
    WOStatus.PENDING_PARTS:  [WOStatus.IN_PROGRESS, WOStatus.CANCELLED],
    WOStatus.COMPLETED:      [],
    WOStatus.CANCELLED:      [],
}


def _generate_wo_number() -> str:
    from datetime import date
    return f"WO-{date.today().year}-{str(uuid.uuid4().int)[:4].upper()}"


@router.get("/", response_model=List[WorkOrderResponse])
async def list_work_orders(
    center_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    asset_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    stmt = select(WorkOrder)
    filters = []
    if center_id:   filters.append(WorkOrder.center_id == center_id)
    if status_filter: filters.append(WorkOrder.status == status_filter)
    if priority:    filters.append(WorkOrder.priority == priority)
    if asset_id:    filters.append(WorkOrder.asset_id == asset_id)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.offset(skip).limit(limit).order_by(WorkOrder.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    payload: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG, Role.TECHNICIAN)),
):
    wo = WorkOrder(
        wo_number=_generate_wo_number(),
        created_by_id=current_user.get("sub"),
        **payload.model_dump(),
    )
    db.add(wo)
    await db.flush()
    # Publish to Kafka for downstream agents
    await publish_event("ger2.wo.commands", {
        "event": "wo.created",
        "wo_id": wo.id,
        "wo_number": wo.wo_number,
        "asset_id": wo.asset_id,
        "priority": wo.priority,
        "wo_type": wo.wo_type,
        "center_id": wo.center_id,
    })
    await cache_invalidate_pattern("workorders:*")
    return wo


@router.patch("/{wo_id}", response_model=WorkOrderResponse)
async def update_work_order(
    wo_id: str,
    payload: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG, Role.TECHNICIAN)),
):
    wo = await db.get(WorkOrder, wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    if payload.status:
        allowed = [s.value for s in WO_VALID_TRANSITIONS.get(wo.status, [])]
        if payload.status not in allowed:
            raise HTTPException(status_code=422, detail=f"Transition {wo.status} → {payload.status} is not allowed")
    # Compute total cost
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(wo, field, value)
    if wo.labor_cost is not None and wo.parts_cost is not None:
        wo.total_cost = (wo.labor_cost or 0) + (wo.parts_cost or 0)
    if payload.status == WOStatus.COMPLETED:
        wo.actual_end = datetime.now(tz=timezone.utc).isoformat()
        await publish_event("ger2.wo.commands", {"event": "wo.completed", "wo_id": wo_id})
    await cache_invalidate_pattern("workorders:*")
    return wo


@router.get("/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(
    wo_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    wo = await db.get(WorkOrder, wo_id)
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return wo
