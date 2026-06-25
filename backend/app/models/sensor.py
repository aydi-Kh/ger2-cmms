
"""
SensorReading — stored in TimescaleDB hypertable partitioned by time.
AIInference — records each agent inference result.
"""
from sqlalchemy import String, Float, JSON, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

class SensorReading(Base, UUIDMixin):
    __tablename__ = "sensor_readings"
    # TimescaleDB: SELECT create_hypertable('sensor_readings', 'timestamp_utc');
    __table_args__ = (Index("ix_sensor_asset_time", "asset_id", "timestamp_utc"),)
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    timestamp_utc: Mapped[str] = mapped_column(String(30), nullable=False)
    sensor_type: Mapped[str] = mapped_column(String(50), nullable=False)   # temperature, vibration, pressure, ...
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    opcua_node_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quality: Mapped[str | None] = mapped_column(String(20), nullable=True)  # good / uncertain / bad
    asset: Mapped["Asset"] = relationship("Asset", back_populates="sensor_readings", foreign_keys=[asset_id])

class AIInference(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ai_inferences"
    asset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String(50), nullable=False)      # predictor / scheduler / ...
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    inference_type: Mapped[str] = mapped_column(String(50), nullable=False) # rul / anomaly / cost_forecast
    rul_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    shap_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triggered_wo_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    asset: Mapped["Asset"] = relationship("Asset", back_populates="ai_inferences", foreign_keys=[asset_id])
