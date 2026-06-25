"""
GER2 CMMS — AI Agents API Router
Endpoints: agent status, latest inferences, SHAP values, event log, trigger manual inference.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import require_roles, Role
from app.models.sensor import AIInference
from app.integrations.kafka.producer import publish_event

router = APIRouter(prefix="/ai", tags=["AI Agents"])

AGENT_REGISTRY = {
    "predictor":   {"name": "Predictor Agent",   "model": "LSTM + Kaplan-Meier ensemble", "version": "1.3.2"},
    "scheduler":   {"name": "Scheduler Agent",   "model": "Constraint satisfaction + FHIR R4", "version": "1.1.0"},
    "cost":        {"name": "Cost Agent",        "model": "XGBoost regression", "version": "1.0.4"},
    "compliance":  {"name": "Compliance Agent",  "model": "Rule engine + NLP", "version": "1.2.1"},
    "diagnostics": {"name": "Diagnostics Agent", "model": "Isolation Forest + CNN", "version": "1.4.0"},
}


@router.get("/agents", summary="List all registered AI agents and their status")
async def list_agents(_: dict = Depends(require_roles(*Role.ALL_ROLES))):
    return list(AGENT_REGISTRY.values()) + [{"id": k, **v} for k, v in AGENT_REGISTRY.items()]


@router.get("/agents/{agent_id}", summary="Get agent details and last heartbeat")
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    result = await db.execute(
        select(AIInference)
        .where(AIInference.agent_id == agent_id)
        .order_by(AIInference.created_at.desc())
        .limit(1)
    )
    last = result.scalar_one_or_none()
    return {
        **AGENT_REGISTRY[agent_id],
        "agent_id": agent_id,
        "last_inference": last.created_at if last else None,
        "status": "active",
    }


@router.get("/agents/{agent_id}/inferences", response_model=List[dict])
async def get_agent_inferences(
    agent_id: str,
    asset_id: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_roles(*Role.ALL_ROLES)),
):
    stmt = select(AIInference).where(AIInference.agent_id == agent_id)
    if asset_id:
        stmt = stmt.where(AIInference.asset_id == asset_id)
    stmt = stmt.order_by(AIInference.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    inferences = result.scalars().all()
    return [
        {
            "id": i.id, "asset_id": i.asset_id, "rul_days": i.rul_days,
            "anomaly_score": i.anomaly_score, "confidence": i.confidence,
            "shap_values": i.shap_values, "created_at": i.created_at,
        }
        for i in inferences
    ]


@router.post("/agents/{agent_id}/trigger", summary="Trigger a manual inference run for an asset")
async def trigger_inference(
    agent_id: str,
    asset_id: str,
    current_user: dict = Depends(require_roles(Role.ADMIN, Role.BIOMEDICAL_ENG)),
):
    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail="Agent not found")
    await publish_event("ger2.agent.events", {
        "event": "inference.requested",
        "agent_id": agent_id,
        "asset_id": asset_id,
        "requested_by": current_user.get("sub"),
        "priority": "high",
    })
    return {"status": "triggered", "agent_id": agent_id, "asset_id": asset_id}
