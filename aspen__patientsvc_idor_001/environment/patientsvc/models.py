from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class MedRecord(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    status: str
    visibility: str
    diagnosis: str
    medications: list[str]
    lab_results: dict[str, str]
    clinical_notes: str
    insurance_id: str
    attachments: dict[str, str]


class MedRecordCreate(BaseModel):
    doctor_id: str = ""
    status: str = "active"
    visibility: str = "private"
    diagnosis: str = ""
    medications: list[str] = []
    lab_results: dict[str, str] = {}
    clinical_notes: str = ""
    insurance_id: str = ""
    attachments: dict[str, str] = {}


class MedRecordPatch(BaseModel):
    status: Optional[str] = None
    visibility: Optional[str] = None
    diagnosis: Optional[str] = None
    medications: Optional[list[str]] = None
    clinical_notes: Optional[str] = None


class ReferRequest(BaseModel):
    doctor_id: str
