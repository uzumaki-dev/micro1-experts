from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from timesheetsvc import store
from timesheetsvc.models import Timesheet, TimesheetCreate, TimesheetPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/timesheets", status_code=201)
def create_timesheet(body: TimesheetCreate, x_user_id: str = Header(...)) -> Timesheet:
    return store.create(
        owner_id=x_user_id,
        project=body.project,
        status=body.status,
        entries=body.entries,
        internal_notes=body.internal_notes,
        private_rate=body.private_rate,
        receipts=body.receipts,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/timesheets")
def list_timesheets(x_user_id: str = Header(...)) -> list[Timesheet]:
    return store.list_all()


@app.get("/timesheets/search")
def search_timesheets(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Timesheet]:
    q_lower = q.lower()
    return [
        ts
        for ts in store.list_all()
        if q_lower in ts.project.lower() or q_lower in ts.internal_notes.lower()
    ]


@app.get("/timesheets/{timesheet_id}")
def get_timesheet(timesheet_id: str, x_user_id: str = Header(...)) -> Timesheet:
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    return ts


@app.get("/timesheets/{timesheet_id}/entries")
def get_entries(timesheet_id: str, x_user_id: str = Header(...)):
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    return ts.entries


@app.get("/timesheets/{timesheet_id}/export")
def export_timesheet(
    timesheet_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "project", "status", "internal_notes", "private_rate",
            "description", "hours", "rate_code", "discount_code",
        ])
        for entry in ts.entries:
            writer.writerow([
                ts.id, ts.project, ts.status, ts.internal_notes, ts.private_rate,
                entry.description, entry.hours, entry.rate_code, entry.discount_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return ts


@app.get("/timesheets/{timesheet_id}/receipts")
def get_receipt(
    timesheet_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    content = ts.receipts.get(name)
    if content is None:
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_ts in store.list_all():
                other_content = other_ts.receipts.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Receipt not found")
    return PlainTextResponse(content)


@app.patch("/timesheets/{timesheet_id}")
def patch_timesheet(
    timesheet_id: str, body: TimesheetPatch, x_user_id: str = Header(...)
) -> Timesheet:
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and ts.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(timesheet_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/timesheets/{timesheet_id}/clone", status_code=201)
def clone_timesheet(timesheet_id: str, x_user_id: str = Header(...)) -> Timesheet:
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    return store.create(
        owner_id=x_user_id,
        project=ts.project,
        status="draft",
        entries=ts.entries,
        internal_notes=ts.internal_notes,
        private_rate=ts.private_rate,
        receipts=ts.receipts,
        collaborators=[],
        visibility="private",
    )


@app.post("/timesheets/{timesheet_id}/submit")
def submit_timesheet(timesheet_id: str, x_user_id: str = Header(...)) -> Timesheet:
    ts = store.get(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and ts.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(timesheet_id, status="submitted")
    return updated  # type: ignore[return-value]
