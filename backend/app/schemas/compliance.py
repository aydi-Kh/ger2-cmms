
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class CertStatusEnum(str, Enum):
    VALID = "valid"
    EXPIRED = "expired"
    NEAR_EXPIRY = "near_expiry"

class CertCreate(BaseModel):
    asset_id: str
    cert_type: str
    cert_number: str
    issue_date: str
    expiry_date: str
    issuing_body: Optional[str] = None
    pdf_url: Optional[str] = None

class CertResponse(BaseModel):
    id: str
    asset_id: str
    cert_type: str
    cert_number: str
    issue_date: str
    expiry_date: str
    status: CertStatusEnum
    issuing_body: Optional[str] = None
    pdf_url: Optional[str] = None
    digital_signature: Optional[str] = None
    created_at: str
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: str
    timestamp_utc: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    class Config:
        from_attributes = True
