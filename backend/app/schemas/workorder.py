
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum

class WOStatusEnum(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WOTypeEnum(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    AI_TRIGGERED = "ai_triggered"
    CALIBRATION = "calibration"
    EMERGENCY = "emergency"

class WOPriorityEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class WorkOrderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    wo_type: WOTypeEnum
    priority: WOPriorityEnum = WOPriorityEnum.MEDIUM
    asset_id: str
    center_id: str
    scheduled_start: Optional[str] = None
    estimated_hours: Optional[float] = None
    checklist: Optional[List[dict]] = None
    ai_trigger_ref: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    status: Optional[WOStatusEnum] = None
    assigned_to_id: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    actual_hours: Optional[float] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    parts_used: Optional[List[dict]] = None
    completion_notes: Optional[str] = None
    checklist: Optional[List[dict]] = None

class WorkOrderResponse(BaseModel):
    id: str
    wo_number: str
    title: str
    status: WOStatusEnum
    wo_type: WOTypeEnum
    priority: WOPriorityEnum
    asset_id: str
    center_id: str
    assigned_to_id: Optional[str] = None
    scheduled_start: Optional[str] = None
    estimated_hours: Optional[float] = None
    total_cost: Optional[float] = None
    ai_trigger_ref: Optional[str] = None
    created_at: str
    updated_at: str
    class Config:
        from_attributes = True
