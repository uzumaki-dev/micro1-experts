from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from patientsvc import store
from patientsvc.models import MedRecord, MedRecordCreate, MedRecordPatch, ReferRequest

app = FastAPI()

ADMIN = "admin"


@app.post("/records", status_code=201)
def create_record(body: MedRecordCreate, x_user_id: str = Header(...)) -> MedRecord:
    return store.create(
        patient_id=x_user_id,
        doctor_id=body.doctor_id,
        status=body.status,
        visibility=body.visibility,
        diagnosis=body.diagnosis,
        medications=body.medications,
        lab_results=body.lab_results,
        clinical_notes=body.clinical_notes,
        insurance_id=body.insurance_id,
        attachments=body.attachments,
    )


@app.get("/records")
def list_records(x_user_id: str = Header(...)) -> list[MedRecord]:
    # BUG: returns all records regardless of ownership
    return store.list_all()


@app.get("/records/search")
def search_records(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[MedRecord]:
    # BUG: searches across all records regardless of ownership
    q_lower = q.lower()
    return [
        r for r in store.list_all()
        if q_lower in r.diagnosis.lower() or q_lower in r.clinical_notes.lower()
    ]


@app.get("/records/{record_id}")
def get_record(record_id: str, x_user_id: str = Header(...)) -> MedRecord:
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any record
    return record


@app.get("/records/{record_id}/labs")
def get_labs(record_id: str, x_user_id: str = Header(...)):
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return record.lab_results


@app.get("/records/{record_id}/medications")
def get_medications(record_id: str, x_user_id: str = Header(...)):
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return record.medications


@app.get("/records/{record_id}/export")
def export_record(
    record_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "patient_id", "doctor_id", "status",
            "diagnosis", "clinical_notes", "insurance_id",
        ])
        writer.writerow([
            record.id, record.patient_id, record.doctor_id, record.status,
            record.diagnosis, record.clinical_notes, record.insurance_id,
        ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return record


@app.get("/records/{record_id}/attachments")
def get_attachment(
    record_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = record.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all records
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_rec in store.list_all():
                other_content = other_rec.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.post("/records/{record_id}/refer", status_code=201)
def refer_record(
    record_id: str, body: ReferRequest, x_user_id: str = Header(...)
) -> MedRecord:
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: copies private fields verbatim — attacker owns the copy
    return store.create(
        patient_id=x_user_id,
        doctor_id=body.doctor_id,
        status="active",
        visibility="private",
        diagnosis=record.diagnosis,        # BUG: copies private diagnosis
        medications=record.medications,    # BUG: copies private medications
        lab_results=record.lab_results,    # BUG: copies private lab results
        clinical_notes=record.clinical_notes,  # BUG: copies private notes
        insurance_id=record.insurance_id,  # BUG: copies private insurance ID
        attachments={},
    )


@app.patch("/records/{record_id}")
def patch_record(
    record_id: str, body: MedRecordPatch, x_user_id: str = Header(...)
) -> MedRecord:
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    if (x_user_id != ADMIN
            and record.patient_id != x_user_id
            and record.doctor_id != x_user_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(record_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/records/{record_id}/archive")
def archive_record(record_id: str, x_user_id: str = Header(...)) -> MedRecord:
    record = store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and record.patient_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(record_id, status="archived")
    return updated  # type: ignore[return-value]
