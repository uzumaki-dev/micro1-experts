from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from expensesvc import store
from expensesvc.models import Expense, ExpenseCreate, ExpensePatch

app = FastAPI()

ADMIN = "admin"


@app.post("/expenses", status_code=201)
def create_expense(body: ExpenseCreate, x_user_id: str = Header(...)) -> Expense:
    return store.create(
        owner_id=x_user_id,
        merchant=body.merchant,
        status=body.status,
        line_items=body.line_items,
        private_notes=body.private_notes,
        policy_code=body.policy_code,
        receipts=body.receipts,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/expenses")
def list_expenses(x_user_id: str = Header(...)) -> list[Expense]:
    # BUG: returns all expenses regardless of ownership
    return store.list_all()


@app.get("/expenses/search")
def search_expenses(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Expense]:
    # BUG: searches across all expenses regardless of ownership
    q_lower = q.lower()
    return [
        exp
        for exp in store.list_all()
        if q_lower in exp.merchant.lower() or q_lower in exp.private_notes.lower()
    ]


@app.get("/expenses/{expense_id}")
def get_expense(expense_id: str, x_user_id: str = Header(...)) -> Expense:
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any expense
    return exp


@app.get("/expenses/{expense_id}/line-items")
def get_line_items(expense_id: str, x_user_id: str = Header(...)):
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    return exp.line_items


@app.get("/expenses/{expense_id}/export")
def export_expense(
    expense_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "merchant", "status", "private_notes", "policy_code",
            "description", "amount", "cost_code", "discount_code",
        ])
        for item in exp.line_items:
            writer.writerow([
                exp.id, exp.merchant, exp.status, exp.private_notes, exp.policy_code,
                item.description, item.amount, item.cost_code, item.discount_code,
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return exp


@app.get("/expenses/{expense_id}/receipts")
def get_receipt(
    expense_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = exp.receipts.get(name)
    if content is None:
        # BUG: naive path traversal — resolves ../<other_id>/<file> across all expenses
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_exp in store.list_all():
                other_content = other_exp.receipts.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Receipt not found")
    return PlainTextResponse(content)


@app.patch("/expenses/{expense_id}")
def patch_expense(
    expense_id: str, body: ExpensePatch, x_user_id: str = Header(...)
) -> Expense:
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and exp.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(expense_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/expenses/{expense_id}/clone", status_code=201)
def clone_expense(expense_id: str, x_user_id: str = Header(...)) -> Expense:
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits private_notes, policy_code, and receipts from victim without scrubbing
    return store.create(
        owner_id=x_user_id,
        merchant=exp.merchant,
        status="draft",
        line_items=exp.line_items,
        private_notes=exp.private_notes,   # BUG: copies private notes
        policy_code=exp.policy_code,        # BUG: copies private policy code
        receipts=exp.receipts,              # BUG: copies private receipts
        collaborators=[],
        visibility="private",
    )


@app.post("/expenses/{expense_id}/submit")
def submit_expense(expense_id: str, x_user_id: str = Header(...)) -> Expense:
    exp = store.get(expense_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and exp.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(expense_id, status="submitted")
    return updated  # type: ignore[return-value]
