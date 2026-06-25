
from sqlalchemy import String, Boolean, Float, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum

class CertStatus(str, enum.Enum):
    VALID = "valid"
    EXPIRED = "expired"
    NEAR_EXPIRY = "near_expiry"
    REVOKED = "revoked"

class CalibrationCert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "calibration_certs"
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    cert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    cert_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    issue_date: Mapped[str] = mapped_column(String(20), nullable=False)
    expiry_date: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[CertStatus] = mapped_column(SAEnum(CertStatus), default=CertStatus.VALID)
    issuing_body: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    dicom_sr_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    digital_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset: Mapped["Asset"] = relationship("Asset", back_populates="calibration_certs")

class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"
    timestamp_utc: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    old_value: Mapped[dict | None] = mapped_column("old_value", String, nullable=True)
    new_value: Mapped[dict | None] = mapped_column("new_value", String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    immutable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
