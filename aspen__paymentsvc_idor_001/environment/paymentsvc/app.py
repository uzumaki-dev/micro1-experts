from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from paymentsvc import store
from paymentsvc.models import Payment, PaymentCreate, PaymentPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/payments", status_code=201)
def create_payment(body: PaymentCreate, x_user_id: str = Header(...)) -> Payment:
    return store.create(
        owner_id=x_user_id,
        merchant=body.merchant,
        status=body.status,
        line_items=body.line_items,
        private_notes=body.private_notes,
        reference_code=body.reference_code,
        documents=body.documents,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/payments")
def list_payments(x_user_id: str = Header(...)) -> list[Payment]:
    # BUG: returns all payments regardless of ownership
    return store.list_all()


@app.get("/payments/search")
def search_payments(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Payment]:
    # BUG: searches across all payments regardless of ownership
    q_lower = q.lower()
    return [
        pmt
        for pmt in store.list_all()
        if q_lower in pmt.merchant.lower() or q_lower in pmt.private_notes.lower()
    ]


@app.get("/payments/{payment_id}")
def get_payment(payment_id: str, x_user_id: str = Header(...)) -> Payment:
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any payment
    return pmt


@app.get("/payments/{payment_id}/line-items")
def get_line_items(payment_id: str, x_user_id: str = Header(...)):
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return pmt.line_items


@app.get("/payments/{payment_id}/export")
def export_payment(
    payment_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "merchant", "status", "private_notes", "reference_code",
            "description", "amount", "fee_code", "category_code",
        ])
        for item in pmt.line_items:
            writer.writerow([
                pmt.id, pmt.merchant, pmt.status, pmt.private_notes, pmt.reference_code,
                item.description, item.amount, item.fee_code, item.category_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return pmt


@app.get("/payments/{payment_id}/documents")
def get_document(
    payment_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = pmt.documents.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all payments
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_pmt in store.list_all():
                other_content = other_pmt.documents.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(content)


@app.patch("/payments/{payment_id}")
def patch_payment(
    payment_id: str, body: PaymentPatch, x_user_id: str = Header(...)
) -> Payment:
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and pmt.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(payment_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/payments/{payment_id}/clone", status_code=201)
def clone_payment(payment_id: str, x_user_id: str = Header(...)) -> Payment:
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits private_notes, reference_code, and documents from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        merchant=pmt.merchant,
        status="pending",
        line_items=pmt.line_items,
        private_notes=pmt.private_notes,    # BUG: copies private notes
        reference_code=pmt.reference_code,  # BUG: copies private reference code
        documents=pmt.documents,            # BUG: copies private documents
        collaborators=[],
        visibility="private",
    )


@app.post("/payments/{payment_id}/void")
def void_payment(payment_id: str, x_user_id: str = Header(...)) -> Payment:
    pmt = store.get(payment_id)
    if pmt is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and pmt.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(payment_id, status="void")
    return updated  # type: ignore[return-value]
