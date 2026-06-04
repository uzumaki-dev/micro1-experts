from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from reportsvc import store
from reportsvc.models import Report, ReportCreate, ReportPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/reports", status_code=201)
def create_report(body: ReportCreate, x_user_id: str = Header(...)) -> Report:
    return store.create(
        owner_id=x_user_id,
        title=body.title,
        status=body.status,
        data_points=body.data_points,
        confidential_notes=body.confidential_notes,
        attachments=body.attachments,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/reports")
def list_reports(x_user_id: str = Header(...)) -> list[Report]:
    # BUG: returns all reports regardless of ownership
    return store.list_all()


@app.get("/reports/search")
def search_reports(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Report]:
    # BUG: searches across all reports regardless of ownership
    q_lower = q.lower()
    return [
        rpt
        for rpt in store.list_all()
        if q_lower in rpt.title.lower() or q_lower in rpt.confidential_notes.lower()
    ]


@app.get("/reports/{report_id}")
def get_report(report_id: str, x_user_id: str = Header(...)) -> Report:
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any report
    return rpt


@app.get("/reports/{report_id}/data-points")
def get_data_points(report_id: str, x_user_id: str = Header(...)):
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return rpt.data_points


@app.get("/reports/{report_id}/export")
def export_report(
    report_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "title", "status", "confidential_notes",
            "label", "value", "metric_code",
        ])
        for dp in rpt.data_points:
            writer.writerow([
                rpt.id, rpt.title, rpt.status, rpt.confidential_notes,
                dp.label, dp.value, dp.metric_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return rpt


@app.get("/reports/{report_id}/attachments")
def get_attachment(
    report_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = rpt.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all reports
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_rpt in store.list_all():
                other_content = other_rpt.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.patch("/reports/{report_id}")
def patch_report(
    report_id: str, body: ReportPatch, x_user_id: str = Header(...)
) -> Report:
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and rpt.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(report_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/reports/{report_id}/fork", status_code=201)
def fork_report(report_id: str, x_user_id: str = Header(...)) -> Report:
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits confidential_notes and attachments from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        title=rpt.title,
        status="draft",
        data_points=rpt.data_points,
        confidential_notes=rpt.confidential_notes,  # BUG: copies private notes
        attachments=rpt.attachments,                # BUG: copies private attachments
        collaborators=[],
        visibility="private",
    )


@app.post("/reports/{report_id}/publish")
def publish_report(report_id: str, x_user_id: str = Header(...)) -> Report:
    rpt = store.get(report_id)
    if rpt is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and rpt.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(report_id, status="published", visibility="public")
    return updated  # type: ignore[return-value]
