from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from invoicesvc import store
from invoicesvc.models import Invoice, InvoiceCreate, InvoicePatch

app = FastAPI()

ADMIN = "admin"


@app.post("/invoices", status_code=201)
def create_invoice(body: InvoiceCreate, x_user_id: str = Header(...)) -> Invoice:
    return store.create(
        owner_id=x_user_id,
        client_name=body.client_name,
        status=body.status,
        line_items=body.line_items,
        internal_notes=body.internal_notes,
        attachments=body.attachments,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/invoices")
def list_invoices(x_user_id: str = Header(...)) -> list[Invoice]:
    # BUG: returns all invoices regardless of ownership
    return store.list_all()


@app.get("/invoices/search")
def search_invoices(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Invoice]:
    # BUG: searches across all invoices regardless of ownership
    q_lower = q.lower()
    return [
        inv
        for inv in store.list_all()
        if q_lower in inv.client_name.lower() or q_lower in inv.internal_notes.lower()
    ]


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str, x_user_id: str = Header(...)) -> Invoice:
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any invoice
    return inv


@app.get("/invoices/{invoice_id}/line-items")
def get_line_items(invoice_id: str, x_user_id: str = Header(...)):
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return inv.line_items


@app.get("/invoices/{invoice_id}/export")
def export_invoice(
    invoice_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "client_name", "status", "internal_notes",
            "description", "quantity", "unit_price", "cost_code", "discount_code",
        ])
        for item in inv.line_items:
            writer.writerow([
                inv.id, inv.client_name, inv.status, inv.internal_notes,
                item.description, item.quantity, item.unit_price,
                item.cost_code, item.discount_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return inv


@app.get("/invoices/{invoice_id}/attachments")
def get_attachment(
    invoice_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = inv.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all invoices
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_inv in store.list_all():
                other_content = other_inv.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.patch("/invoices/{invoice_id}")
def patch_invoice(
    invoice_id: str, body: InvoicePatch, x_user_id: str = Header(...)
) -> Invoice:
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and inv.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(invoice_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/invoices/{invoice_id}/duplicate", status_code=201)
def duplicate_invoice(invoice_id: str, x_user_id: str = Header(...)) -> Invoice:
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits internal_notes and attachments from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        client_name=inv.client_name,
        status="draft",
        line_items=inv.line_items,
        internal_notes=inv.internal_notes,   # BUG: copies private notes
        attachments=inv.attachments,          # BUG: copies private attachments
        collaborators=[],
        visibility="private",
    )


@app.post("/invoices/{invoice_id}/share")
def share_invoice(invoice_id: str, x_user_id: str = Header(...)) -> Invoice:
    inv = store.get(invoice_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and inv.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(invoice_id, visibility="public")
    return updated  # type: ignore[return-value]
