"""
GER2 CMMS — Application Configuration
Centralises all environment-driven settings via pydantic-settings.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──
    APP_NAME: str = "GER2 CMMS API"
    APP_VERSION: str = "2.4.1"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://cmms.ger2.tn"]

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://ger2:ger2pass@localhost:5432/ger2_cmms"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_DEFAULT: int = 300           # seconds
    CACHE_TTL_ASSETS: int = 60
    CACHE_TTL_DASHBOARD: int = 30

    # ── Kafka ──
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "ger2-cmms-backend"
    KAFKA_TOPIC_SENSOR_RAW: str = "ger2.sensor.raw"
    KAFKA_TOPIC_AGENT_EVENTS: str = "ger2.agent.events"
    KAFKA_TOPIC_WO_COMMANDS: str = "ger2.wo.commands"
    KAFKA_TOPIC_COMPLIANCE_EVENTS: str = "ger2.compliance.events"
    KAFKA_TOPIC_COST_EVENTS: str = "ger2.cost.events"
    KAFKA_TOPIC_DICOM_EVENTS: str = "ger2.dicom.events"
    KAFKA_TOPIC_AUDIT_LOG: str = "ger2.audit.log"

    # ── Security / JWT ──
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_32_BYTES_MIN"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 12

    # ── DICOM ──
    DICOM_AE_TITLE: str = "GER2_CMMS"
    DICOM_WADO_RS_URL: str = "http://orthanc:8042/wado"
    DICOM_STOW_RS_URL: str = "http://orthanc:8042/instances"
    DICOM_ANONYMISATION_PROFILE: str = "PS3.15_Profile_E"

    # ── OPC-UA ──
    OPCUA_SERVER_URL: str = "opc.tcp://opcua-server:4840"
    OPCUA_SECURITY_POLICY: str = "Basic256Sha256"
    OPCUA_SECURITY_MODE: str = "SignAndEncrypt"
    OPCUA_POLL_INTERVAL_SECONDS: int = 5

    # ── FHIR ──
    FHIR_SERVER_URL: str = "http://fhir:8080/fhir"
    FHIR_VERSION: str = "R4"

    # ── MLflow / Model Registry ──
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    MODEL_RUL_PATH: str = "/models/rul_ensemble.onnx"
    MODEL_ANOMALY_PATH: str = "/models/anomaly_detector.onnx"

    # ── Observability ──
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    JAEGER_ENDPOINT: str = "http://jaeger:14268/api/traces"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
