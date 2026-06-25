
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class AssetStatusEnum(str, Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    DECOMMISSIONED = "decommissioned"

class AssetBase(BaseModel):
    asset_code: str = Field(..., example="GER2-MRI-001")
    name: str
    manufacturer: str
    model: str
    serial_number: str
    category: str
    center_id: str
    location_room: str
    location_floor: Optional[str] = None
    install_date: Optional[str] = None
    acquisition_cost: Optional[float] = None
    dicom_ae_title: Optional[str] = None
    opcua_node_id: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[AssetStatusEnum] = None
    location_room: Optional[str] = None
    next_pm_date: Optional[str] = None
    assigned_technician_id: Optional[str] = None
    notes: Optional[str] = None

class AssetResponse(AssetBase):
    id: str
    status: AssetStatusEnum
    rul_score: Optional[float] = None
    rul_computed_at: Optional[str] = None
    next_pm_date: Optional[str] = None
    created_at: str
    updated_at: str
    class Config:
        from_attributes = True
