"""
GER2 CMMS — Compliance & Audit Router
Endpoints: calibration certificates, audit trail, evidence pack generation.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import require_roles, Role
from app.models.compliance import CalibrationCert, AuditLog
from app.schemas.compliance import CertCreate, CertResponse, AuditLogResponse

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.get("/certificates", response_model=List[CertResponse])
async def list_certificates(
    asset_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    stmt = select(CalibrationCert)
    if asset_id:
        stmt = stmt.where(CalibrationCert.asset_id == asset_id)
    if status_filter:
        stmt = stmt.where(CalibrationCert.status == status_filter)
    stmt = stmt.order_by(CalibrationCert.expiry_date)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/certificates", response_model=CertResponse, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    payload: CertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG, Role.AUDITOR)),
):
    cert = CalibrationCert(**payload.model_dump())
    db.add(cert)
    await db.flush()
    return cert


@router.get("/audit-trail", response_model=List[AuditLogResponse])
async def get_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG, Role.AUDITOR)),
):
    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    stmt = stmt.order_by(AuditLog.timestamp_utc.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/evidence-pack/{asset_id}", summary="Generate regulatory evidence pack for an asset")
async def generate_evidence_pack(
    asset_id: str,
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG, Role.AUDITOR)),
):
    """Async job: compiles calibration certs, WO history, audit trail into a signed PDF."""
    from app.integrations.kafka.producer import publish_event
    await publish_event("ger2.compliance.events", {
        "event": "evidence_pack.requested",
        "asset_id": asset_id,
        "requested_by": current_user.get("sub"),
    })
    return {"status": "queued", "asset_id": asset_id, "message": "Evidence pack generation started. You will be notified on completion."}
