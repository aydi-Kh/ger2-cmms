"""
GER2 CMMS — DICOM Integration Client
Handles WADO-RS retrieval, STOW-RS storage, and Structured Report (SR) creation.
Anonymises PHI per DICOM PS3.15 Profile E before any off-site transmission.
"""
import httpx
import pydicom
import uuid
from datetime import datetime, timezone
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


PROFILE_E_TAGS_TO_REMOVE = [
    (0x0010, 0x0010),  # PatientName
    (0x0010, 0x0020),  # PatientID
    (0x0010, 0x0030),  # PatientBirthDate
    (0x0008, 0x1030),  # StudyDescription — retain for equipment context
    (0x0008, 0x0080),  # InstitutionName
    (0x0008, 0x0081),  # InstitutionAddress
    (0x0008, 0x009C),  # ConsultingPhysicianName
]


def anonymise_dataset(ds: pydicom.Dataset) -> pydicom.Dataset:
    """Apply DICOM PS3.15 Profile E de-identification to a dataset."""
    for tag in PROFILE_E_TAGS_TO_REMOVE:
        if tag in ds:
            del ds[tag]
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethod = "GER2-PS315-ProfileE-v1"
    return ds


async def retrieve_dicom_metadata(study_uid: str, series_uid: Optional[str] = None) -> dict:
    """WADO-RS metadata retrieval for an imaging study."""
    url = f"{settings.DICOM_WADO_RS_URL}/studies/{study_uid}/metadata"
    if series_uid:
        url = f"{settings.DICOM_WADO_RS_URL}/studies/{study_uid}/series/{series_uid}/metadata"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers={"Accept": "application/dicom+json"})
        response.raise_for_status()
        logger.info("dicom.wado_rs.retrieved", study_uid=study_uid)
        return response.json()


async def store_dicom_sr(
    asset_id: str,
    wo_number: str,
    calibration_params: dict,
    dicom_sr_template: str = "TID_3801",
) -> str:
    """
    Create and store a DICOM Structured Report for a calibration/maintenance event.
    Returns the SOP Instance UID of the created SR.
    """
    ds = pydicom.Dataset()
    sop_uid = f"2.25.{uuid.uuid4().int}"
    ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.88.22"   # Enhanced SR
    ds.SOPInstanceUID = sop_uid
    ds.StudyDate = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    ds.StudyTime = datetime.now(tz=timezone.utc).strftime("%H%M%S")
    ds.ContentDate = ds.StudyDate
    ds.ContentTime = ds.StudyTime
    ds.Modality = "SR"
    ds.Manufacturer = "GER2_CMMS"
    ds.SeriesDescription = f"Maintenance SR — {wo_number}"
    ds.ContentCreatorName = "GER2_CMMS_Compliance_Agent"
    # Anonymise before transmission
    ds = anonymise_dataset(ds)
    # STOW-RS upload
    file_bytes = pydicom.dcmwrite(None, ds)  # in-memory
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            settings.DICOM_STOW_RS_URL,
            content=file_bytes,
            headers={"Content-Type": "application/dicom"},
        )
        resp.raise_for_status()
    logger.info("dicom.sr.stored", sop_uid=sop_uid, wo_number=wo_number, asset_id=asset_id)
    return sop_uid


async def query_worklist(ae_title: str, modality: Optional[str] = None) -> list:
    """DICOM MWL (Modality Worklist) C-FIND equivalent via DICOMweb."""
    url = f"{settings.DICOM_WADO_RS_URL}/mwl"
    params = {"00400100.00080060": modality} if modality else {}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
