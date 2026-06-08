from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from leasesvc import store
from leasesvc.models import Lease, LeaseCreate, LeasePatch

app = FastAPI()

ADMIN = "admin"


@app.post("/leases", status_code=201)
def create_lease(body: LeaseCreate, x_user_id: str = Header(...)) -> Lease:
    return store.create(
        owner_id=x_user_id,
        tenant_name=body.tenant_name,
        property_address=body.property_address,
        status=body.status,
        visibility=body.visibility,
        collaborators=body.collaborators,
        private_notes=body.private_notes,
        clauses=body.clauses,
        attachments=body.attachments,
    )


@app.get("/leases")
def list_leases(x_user_id: str = Header(...)) -> list[Lease]:
    # BUG: returns all leases regardless of ownership
    return store.list_all()


@app.get("/leases/search")
def search_leases(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Lease]:
    # BUG: searches across all leases regardless of ownership
    q_lower = q.lower()
    return [
        lease
        for lease in store.list_all()
        if q_lower in lease.tenant_name.lower()
        or q_lower in lease.property_address.lower()
        or q_lower in lease.private_notes.lower()
    ]


@app.get("/leases/{lease_id}")
def get_lease(lease_id: str, x_user_id: str = Header(...)) -> Lease:
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any lease
    return lease


@app.get("/leases/{lease_id}/clauses")
def get_clauses(lease_id: str, x_user_id: str = Header(...)):
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check, leaks clause_code
    return lease.clauses


@app.get("/leases/{lease_id}/export")
def export_lease(
    lease_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "tenant_name", "owner_id", "status", "private_notes",
            "description", "clause_code",
        ])
        for clause in lease.clauses:
            writer.writerow([
                lease.id, lease.tenant_name, lease.owner_id, lease.status,
                lease.private_notes, clause.description, clause.clause_code,
            ])
        if not lease.clauses:
            writer.writerow([
                lease.id, lease.tenant_name, lease.owner_id, lease.status,
                lease.private_notes, "", "",
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return lease


@app.get("/leases/{lease_id}/documents")
def get_document(
    lease_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = lease.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — discards path prefix, scans all leases
        # for the last path component (filename across all leases)
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_lease in store.list_all():
                other_content = other_lease.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(content)


@app.patch("/leases/{lease_id}")
def patch_lease(
    lease_id: str, body: LeasePatch, x_user_id: str = Header(...)
) -> Lease:
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and lease.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(lease_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/leases/{lease_id}/clone", status_code=201)
def clone_lease(lease_id: str, x_user_id: str = Header(...)) -> Lease:
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits private_notes, clauses (with clause_code), attachments verbatim
    return store.create(
        owner_id=x_user_id,
        tenant_name=lease.tenant_name,
        property_address=lease.property_address,
        status="draft",
        visibility="private",
        private_notes=lease.private_notes,  # BUG: copies private notes
        clauses=lease.clauses,              # BUG: copies clauses with private clause_code
        attachments=lease.attachments,      # BUG: copies private attachments
    )


@app.post("/leases/{lease_id}/renew")
def renew_lease(lease_id: str, x_user_id: str = Header(...)) -> Lease:
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and lease.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(lease_id, status="active")
    return updated  # type: ignore[return-value]


@app.post("/leases/{lease_id}/share")
def share_lease(lease_id: str, x_user_id: str = Header(...)) -> Lease:
    lease = store.get(lease_id)
    if lease is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check, returns full lease including private_notes
    return lease
