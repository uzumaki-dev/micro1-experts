from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from budgetsvc import store
from budgetsvc.models import Budget, BudgetCreate, BudgetPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/budgets", status_code=201)
def create_budget(body: BudgetCreate, x_user_id: str = Header(...)) -> Budget:
    return store.create(
        owner_id=x_user_id,
        name=body.name,
        status=body.status,
        items=body.items,
        budget_memo=body.budget_memo,
        fiscal_code=body.fiscal_code,
        attachments=body.attachments,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/budgets")
def list_budgets(x_user_id: str = Header(...)) -> list[Budget]:
    # BUG: returns all budgets regardless of ownership
    return store.list_all()


@app.get("/budgets/search")
def search_budgets(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Budget]:
    # BUG: searches across all budgets regardless of ownership
    q_lower = q.lower()
    return [
        b
        for b in store.list_all()
        if q_lower in b.name.lower() or q_lower in b.budget_memo.lower()
    ]


@app.get("/budgets/{budget_id}")
def get_budget(budget_id: str, x_user_id: str = Header(...)) -> Budget:
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any budget
    return b


@app.get("/budgets/{budget_id}/items")
def get_items(budget_id: str, x_user_id: str = Header(...)):
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return b.items


@app.get("/budgets/{budget_id}/export")
def export_budget(
    budget_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "name", "status", "budget_memo", "fiscal_code",
            "description", "amount", "allocation_code", "discount_code",
        ])
        for item in b.items:
            writer.writerow([
                b.id, b.name, b.status, b.budget_memo, b.fiscal_code,
                item.description, item.amount, item.allocation_code, item.discount_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return b


@app.get("/budgets/{budget_id}/attachments")
def get_attachment(
    budget_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = b.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all budgets
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_b in store.list_all():
                other_content = other_b.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.patch("/budgets/{budget_id}")
def patch_budget(
    budget_id: str, body: BudgetPatch, x_user_id: str = Header(...)
) -> Budget:
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and b.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(budget_id, **updates)
    return updated


@app.post("/budgets/{budget_id}/clone", status_code=201)
def clone_budget(budget_id: str, x_user_id: str = Header(...)) -> Budget:
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits budget_memo, fiscal_code, and attachments without scrubbing
    return store.create(
        owner_id=x_user_id,
        name=b.name,
        status="draft",
        items=b.items,
        budget_memo=b.budget_memo,
        fiscal_code=b.fiscal_code,
        attachments=b.attachments,
        collaborators=[],
        visibility="private",
    )


@app.post("/budgets/{budget_id}/submit")
def submit_budget(budget_id: str, x_user_id: str = Header(...)) -> Budget:
    b = store.get(budget_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and b.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(budget_id, status="submitted")
    return updated
