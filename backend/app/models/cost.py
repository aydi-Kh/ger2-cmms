
from sqlalchemy import String, Float, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum

class CostType(str, enum.Enum):
    LABOR = "labor"
    PARTS = "parts"
    CONTRACTOR = "contractor"
    ENERGY = "energy"
    CALIBRATION = "calibration"

class CostRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "cost_records"
    wo_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    center_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    cost_type: Mapped[CostType] = mapped_column(SAEnum(CostType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="TND")
    period_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", String, nullable=True)
