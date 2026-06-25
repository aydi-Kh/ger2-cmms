
from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BIOMEDICAL_ENG = "biomedical_engineer"
    TECHNICIAN = "technician"
    AUDITOR = "auditor"
    READONLY = "readonly"

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.READONLY)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    center_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
