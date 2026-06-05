from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from workordersvc import store
from workordersvc.models import WorkOrder, WorkOrderCreate, WorkOrderPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/workorders", status_code=201)
def create_workorder(body: WorkOrderCreate, x_user_id: str = Header(...)) -> WorkOrder:
    return store.create(
        owner_id=x_user_id,
        title=body.title,
        status=body.status,
        entries=body.entries,
        internal_notes=body.internal_notes,
        private_rate=body.private_rate,
        documents=body.documents,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/workorders")
def list_workorders(x_user_id: str = Header(...)) -> list[WorkOrder]:
    # BUG: returns all workorders regardless of ownership
    return store.list_all()


@app.get("/workorders/search")
def search_workorders(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[WorkOrder]:
    # BUG: searches across all workorders regardless of ownership
    q_lower = q.lower()
    return [
        wo
        for wo in store.list_all()
        if q_lower in wo.title.lower() or q_lower in wo.internal_notes.lower()
    ]


@app.get("/workorders/{workorder_id}")
def get_workorder(workorder_id: str, x_user_id: str = Header(...)) -> WorkOrder:
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any workorder
    return wo


@app.get("/workorders/{workorder_id}/entries")
def get_entries(workorder_id: str, x_user_id: str = Header(...)):
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return wo.entries


@app.get("/workorders/{workorder_id}/export")
def export_workorder(
    workorder_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "title", "status", "internal_notes", "private_rate",
            "description", "hours", "labor_code", "discount_code",
        ])
        for entry in wo.entries:
            writer.writerow([
                wo.id, wo.title, wo.status, wo.internal_notes, wo.private_rate,
                entry.description, entry.hours, entry.labor_code, entry.discount_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return wo


@app.get("/workorders/{workorder_id}/documents")
def get_document(
    workorder_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = wo.documents.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all workorders
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_wo in store.list_all():
                other_content = other_wo.documents.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(content)


@app.patch("/workorders/{workorder_id}")
def patch_workorder(
    workorder_id: str, body: WorkOrderPatch, x_user_id: str = Header(...)
) -> WorkOrder:
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and wo.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(workorder_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/workorders/{workorder_id}/clone", status_code=201)
def clone_workorder(workorder_id: str, x_user_id: str = Header(...)) -> WorkOrder:
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits internal_notes, private_rate, and documents from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        title=wo.title,
        status="open",
        entries=wo.entries,
        internal_notes=wo.internal_notes,    # BUG: copies private notes
        private_rate=wo.private_rate,        # BUG: copies private rate
        documents=wo.documents,              # BUG: copies private documents
        collaborators=[],
        visibility="private",
    )


@app.post("/workorders/{workorder_id}/submit")
def submit_workorder(workorder_id: str, x_user_id: str = Header(...)) -> WorkOrder:
    wo = store.get(workorder_id)
    if wo is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and wo.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(workorder_id, status="submitted")
    return updated  # type: ignore[return-value]
