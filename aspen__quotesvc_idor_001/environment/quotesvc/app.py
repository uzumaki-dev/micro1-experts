from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from quotesvc import store
from quotesvc.models import Quote, QuoteCreate, QuotePatch

app = FastAPI()

ADMIN = "admin"


@app.post("/quotes", status_code=201)
def create_quote(body: QuoteCreate, x_user_id: str = Header(...)) -> Quote:
    return store.create(
        owner_id=x_user_id,
        client_name=body.client_name,
        status=body.status,
        line_items=body.line_items,
        internal_notes=body.internal_notes,
        terms=body.terms,
        attachments=body.attachments,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/quotes")
def list_quotes(x_user_id: str = Header(...)) -> list[Quote]:
    # BUG: returns all quotes regardless of ownership
    return store.list_all()


@app.get("/quotes/search")
def search_quotes(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Quote]:
    # BUG: searches across all quotes regardless of ownership
    q_lower = q.lower()
    return [
        quote
        for quote in store.list_all()
        if q_lower in quote.client_name.lower() or q_lower in quote.internal_notes.lower()
    ]


@app.get("/quotes/{quote_id}")
def get_quote(quote_id: str, x_user_id: str = Header(...)) -> Quote:
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any quote
    return quote


@app.get("/quotes/{quote_id}/line-items")
def get_line_items(quote_id: str, x_user_id: str = Header(...)):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return quote.line_items


@app.get("/quotes/{quote_id}/export")
def export_quote(
    quote_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "client_name", "status", "internal_notes", "terms",
            "description", "quantity", "unit_price", "vendor_code", "discount_code",
        ])
        for item in quote.line_items:
            writer.writerow([
                quote.id, quote.client_name, quote.status,
                quote.internal_notes, quote.terms,
                item.description, item.quantity, item.unit_price,
                item.vendor_code, item.discount_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return quote


@app.get("/quotes/{quote_id}/attachments")
def get_attachment(
    quote_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = quote.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all quotes
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_quote in store.list_all():
                other_content = other_quote.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.post("/quotes/{quote_id}/fork", status_code=201)
def fork_quote(quote_id: str, x_user_id: str = Header(...)) -> Quote:
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits internal_notes, terms, and attachments from source without scrubbing
    return store.create(
        owner_id=x_user_id,
        client_name=quote.client_name,
        status="draft",
        line_items=quote.line_items,
        internal_notes=quote.internal_notes,   # BUG: copies private notes
        terms=quote.terms,                      # BUG: copies private terms
        attachments=quote.attachments,          # BUG: copies private attachments
        collaborators=[],
        visibility="private",
    )


@app.patch("/quotes/{quote_id}")
def patch_quote(
    quote_id: str, body: QuotePatch, x_user_id: str = Header(...)
) -> Quote:
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and quote.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    return store.update(quote_id, **updates)  # type: ignore[return-value]


@app.post("/quotes/{quote_id}/send")
def send_quote(quote_id: str, x_user_id: str = Header(...)) -> Quote:
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and quote.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return store.update(quote_id, status="sent")  # type: ignore[return-value]
