
from sqlalchemy import String, Float, Integer, Text, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum

class WOStatus(str, enum.Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    PENDING_PARTS = "pending_parts"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WOType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    AI_TRIGGERED = "ai_triggered"
    CALIBRATION = "calibration"
    EMERGENCY = "emergency"

class WOPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class WorkOrder(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "work_orders"
    wo_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WOStatus] = mapped_column(SAEnum(WOStatus), default=WOStatus.BACKLOG, index=True)
    wo_type: Mapped[WOType] = mapped_column(SAEnum(WOType), nullable=False)
    priority: Mapped[WOPriority] = mapped_column(SAEnum(WOPriority), default=WOPriority.MEDIUM)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    assigned_to_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    center_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    scheduled_start: Mapped[str | None] = mapped_column(String(30), nullable=True)
    scheduled_end: Mapped[str | None] = mapped_column(String(30), nullable=True)
    actual_start: Mapped[str | None] = mapped_column(String(30), nullable=True)
    actual_end: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    labor_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    parts_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    checklist: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parts_used: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_trigger_ref: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dicom_sr_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset: Mapped["Asset"] = relationship("Asset", back_populates="work_orders")
