
from sqlalchemy import String, Float, Integer, Text, Boolean, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum

class AssetStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    DECOMMISSIONED = "decommissioned"

class AssetCategory(str, enum.Enum):
    AI_IMAGING = "ai_imaging"
    LABORATORY = "laboratory"
    GENERAL = "general"
    LIFE_SUPPORT = "life_support"
    INFRASTRUCTURE = "infrastructure"

class Asset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (
        Index("ix_assets_center_status", "center_id", "status"),
        Index("ix_assets_category", "category"),
    )
    asset_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[AssetCategory] = mapped_column(SAEnum(AssetCategory), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(SAEnum(AssetStatus), default=AssetStatus.OPERATIONAL)
    center_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    location_room: Mapped[str] = mapped_column(String(100), nullable=False)
    location_floor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    install_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    warranty_expiry: Mapped[str | None] = mapped_column(String(20), nullable=True)
    acquisition_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    dicom_ae_title: Mapped[str | None] = mapped_column(String(64), nullable=True)
    opcua_node_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fhir_device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rul_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rul_computed_at: Mapped[str | None] = mapped_column(String(30), nullable=True)
    next_pm_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    assigned_technician_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    qr_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rfid_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_orders: Mapped[list["WorkOrder"]] = relationship("WorkOrder", back_populates="asset", lazy="select")
    sensor_readings: Mapped[list["SensorReading"]] = relationship("SensorReading", back_populates="asset", lazy="select")
    ai_inferences: Mapped[list["AIInference"]] = relationship("AIInference", back_populates="asset", lazy="select")
    calibration_certs: Mapped[list["CalibrationCert"]] = relationship("CalibrationCert", back_populates="asset", lazy="select")
