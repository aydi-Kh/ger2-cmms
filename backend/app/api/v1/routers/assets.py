"""
GER2 CMMS — Asset Management API Router
Endpoints: CRUD assets, sensor readings, RUL scores, QR/RFID lookup.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import require_roles, Role
from app.core.cache import cache_get, cache_set, cache_invalidate_pattern
from app.core.config import settings
from app.models.asset import Asset, AssetStatus
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    center_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    """List assets with optional filtering. Results cached per query signature."""
    cache_key = f"assets:list:{center_id}:{category}:{status}:{search}:{skip}:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    stmt = select(Asset)
    filters = []
    if center_id:
        filters.append(Asset.center_id == center_id)
    if category:
        filters.append(Asset.category == category)
    if status:
        filters.append(Asset.status == status)
    if search:
        filters.append(
            Asset.name.ilike(f"%{search}%") | Asset.asset_code.ilike(f"%{search}%")
        )
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.offset(skip).limit(limit).order_by(Asset.asset_code)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    data = [AssetResponse.model_validate(a).model_dump() for a in assets]
    await cache_set(cache_key, data, ttl=settings.CACHE_TTL_ASSETS)
    return data


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG)),
):
    asset = Asset(**payload.model_dump())
    db.add(asset)
    await db.flush()
    await cache_invalidate_pattern("assets:list:*")
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG, Role.TECHNICIAN)),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    await cache_invalidate_pattern(f"assets:*")
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def decommission_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(Role.ADMIN)),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.status = AssetStatus.DECOMMISSIONED
    await cache_invalidate_pattern("assets:*")


@router.get("/qr/{qr_code}", response_model=AssetResponse)
async def lookup_by_qr(
    qr_code: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    result = await db.execute(select(Asset).where(Asset.qr_code == qr_code))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="QR code not found")
    return asset


@router.get("/{asset_id}/rul", summary="Get latest RUL inference for an asset")
async def get_asset_rul(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    from app.models.sensor import AIInference
    result = await db.execute(
        select(AIInference)
        .where(AIInference.asset_id == asset_id, AIInference.inference_type == "rul")
        .order_by(AIInference.created_at.desc())
        .limit(1)
    )
    inference = result.scalar_one_or_none()
    if not inference:
        raise HTTPException(status_code=404, detail="No RUL inference available for this asset")
    return {
        "asset_id": asset_id,
        "rul_days": inference.rul_days,
        "confidence": inference.confidence,
        "shap_values": inference.shap_values,
        "model_version": inference.model_version,
        "computed_at": inference.created_at,
    }
