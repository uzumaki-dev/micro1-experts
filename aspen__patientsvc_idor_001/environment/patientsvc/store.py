from __future__ import annotations
import uuid
from patientsvc.models import MedRecord

_records: dict[str, MedRecord] = {}


def reset() -> None:
    _records.clear()


def create(
    patient_id: str,
    doctor_id: str = "",
    status: str = "active",
    visibility: str = "private",
    diagnosis: str = "",
    medications: list[str] | None = None,
    lab_results: dict[str, str] | None = None,
    clinical_notes: str = "",
    insurance_id: str = "",
    attachments: dict[str, str] | None = None,
) -> MedRecord:
    record = MedRecord(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        doctor_id=doctor_id,
        status=status,
        visibility=visibility,
        diagnosis=diagnosis,
        medications=medications or [],
        lab_results=lab_results or {},
        clinical_notes=clinical_notes,
        insurance_id=insurance_id,
        attachments=attachments or {},
    )
    _records[record.id] = record
    return record


def get(record_id: str) -> MedRecord | None:
    return _records.get(record_id)


def list_all() -> list[MedRecord]:
    return list(_records.values())


def update(record_id: str, **kwargs) -> MedRecord | None:
    record = _records.get(record_id)
    if record is None:
        return None
    updated = record.model_copy(update={k: v for k, v in kwargs.items()})
    _records[record_id] = updated
    return updated
