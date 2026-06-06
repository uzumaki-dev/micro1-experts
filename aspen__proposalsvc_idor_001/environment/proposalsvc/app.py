from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from proposalsvc import store
from proposalsvc.models import Proposal, ProposalCreate, ProposalPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/proposals", status_code=201)
def create_proposal(body: ProposalCreate, x_user_id: str = Header(...)) -> Proposal:
    return store.create(
        owner_id=x_user_id,
        client_name=body.client_name,
        status=body.status,
        line_items=body.line_items,
        internal_notes=body.internal_notes,
        discount_pct=body.discount_pct,
        attachments=body.attachments,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/proposals")
def list_proposals(x_user_id: str = Header(...)) -> list[Proposal]:
    # BUG: returns all proposals regardless of ownership
    return store.list_all()


@app.get("/proposals/search")
def search_proposals(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Proposal]:
    # BUG: searches across all proposals regardless of ownership
    q_lower = q.lower()
    return [
        p
        for p in store.list_all()
        if q_lower in p.client_name.lower() or q_lower in p.internal_notes.lower()
    ]


@app.get("/proposals/{proposal_id}")
def get_proposal(proposal_id: str, x_user_id: str = Header(...)) -> Proposal:
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any proposal
    return p


@app.get("/proposals/{proposal_id}/line-items")
def get_line_items(proposal_id: str, x_user_id: str = Header(...)):
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return p.line_items


@app.get("/proposals/{proposal_id}/export")
def export_proposal(
    proposal_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "client_name", "status", "internal_notes", "discount_pct",
            "description", "quantity", "unit_price", "margin_code",
        ])
        for item in p.line_items:
            writer.writerow([
                p.id, p.client_name, p.status, p.internal_notes, p.discount_pct,
                item.description, item.quantity, item.unit_price, item.margin_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return p


@app.get("/proposals/{proposal_id}/attachments")
def get_attachment(
    proposal_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = p.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all proposals
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_p in store.list_all():
                other_content = other_p.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.patch("/proposals/{proposal_id}")
def patch_proposal(
    proposal_id: str, body: ProposalPatch, x_user_id: str = Header(...)
) -> Proposal:
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and p.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(proposal_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/proposals/{proposal_id}/clone", status_code=201)
def clone_proposal(proposal_id: str, x_user_id: str = Header(...)) -> Proposal:
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits internal_notes, discount_pct, and attachments from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        client_name=p.client_name,
        status="draft",
        line_items=p.line_items,
        internal_notes=p.internal_notes,    # BUG: copies private notes
        discount_pct=p.discount_pct,        # BUG: copies private discount
        attachments=p.attachments,          # BUG: copies private attachments
        collaborators=[],
        visibility="private",
    )


@app.post("/proposals/{proposal_id}/send")
def send_proposal(proposal_id: str, x_user_id: str = Header(...)) -> Proposal:
    p = store.get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and p.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(proposal_id, status="sent")
    return updated  # type: ignore[return-value]
