from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from schedulesvc import store
from schedulesvc.models import Schedule, ScheduleCreate, SchedulePatch

app = FastAPI()

ADMIN = "admin"


@app.post("/schedules", status_code=201)
def create_schedule(body: ScheduleCreate, x_user_id: str = Header(...)) -> Schedule:
    return store.create(
        owner_id=x_user_id,
        title=body.title,
        status=body.status,
        visibility=body.visibility,
        internal_notes=body.internal_notes,
        pay_rate=body.pay_rate,
        entries=body.entries,
        attachments=body.attachments,
    )


@app.get("/schedules")
def list_schedules(x_user_id: str = Header(...)) -> list[Schedule]:
    # BUG: returns all schedules regardless of ownership
    return store.list_all()


@app.get("/schedules/search")
def search_schedules(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Schedule]:
    # BUG: searches across all schedules regardless of ownership;
    # also leaks internal_notes content via query-term matching
    q_lower = q.lower()
    return [
        s
        for s in store.list_all()
        if q_lower in s.title.lower() or q_lower in s.internal_notes.lower()
    ]


@app.get("/schedules/{schedule_id}")
def get_schedule(schedule_id: str, x_user_id: str = Header(...)) -> Schedule:
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any schedule
    return s


@app.get("/schedules/{schedule_id}/entries")
def get_entries(schedule_id: str, x_user_id: str = Header(...)):
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return s.entries


@app.get("/schedules/{schedule_id}/export")
def export_schedule(
    schedule_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "title", "owner_id", "status", "internal_notes", "pay_rate",
            "date", "hours", "rate_code",
        ])
        for entry in s.entries:
            writer.writerow([
                s.id, s.title, s.owner_id, s.status, s.internal_notes, s.pay_rate,
                entry.date, entry.hours, entry.rate_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return s


@app.get("/schedules/{schedule_id}/attachments")
def get_attachment(
    schedule_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = s.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — discards path prefix, returns first schedule
        # with a matching filename (filename-wildcard across all schedules)
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_s in store.list_all():
                other_content = other_s.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.patch("/schedules/{schedule_id}")
def patch_schedule(
    schedule_id: str, body: SchedulePatch, x_user_id: str = Header(...)
) -> Schedule:
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and s.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(schedule_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/schedules/{schedule_id}/clone", status_code=201)
def clone_schedule(schedule_id: str, x_user_id: str = Header(...)) -> Schedule:
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits internal_notes, pay_rate, entries (with rate_code) and attachments verbatim
    return store.create(
        owner_id=x_user_id,
        title=s.title,
        status="draft",
        visibility="private",
        internal_notes=s.internal_notes,   # BUG: copies private notes
        pay_rate=s.pay_rate,               # BUG: copies private pay rate
        entries=s.entries,                 # BUG: copies entries with private rate_code
        attachments=s.attachments,         # BUG: copies private attachments
    )


@app.post("/schedules/{schedule_id}/publish")
def publish_schedule(schedule_id: str, x_user_id: str = Header(...)) -> Schedule:
    s = store.get(schedule_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and s.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(schedule_id, status="published")
    return updated  # type: ignore[return-value]
