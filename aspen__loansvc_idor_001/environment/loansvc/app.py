import csv
import io
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse

from loansvc import store
from loansvc.models import LoanCreate, LoanPatch

app = FastAPI()


def _is_admin(user_id: str) -> bool:
    return user_id == "admin"


@app.post("/loans", status_code=201)
def create_loan(body: LoanCreate, x_user_id: str = Header(...)):
    loan_id = str(uuid.uuid4())
    loan = {
        "id": loan_id,
        "owner_id": x_user_id,
        "applicant_name": body.applicant_name,
        "status": "draft",
        "fees": [f.model_dump() for f in body.fees],
        "underwriter_notes": body.underwriter_notes,
        "private_rate": body.private_rate,
        "documents": body.documents,
        "co_applicants": body.co_applicants,
        "visibility": body.visibility,
    }
    store.save_loan(loan)
    return loan


@app.get("/loans")
def list_loans(x_user_id: str = Header(...)):
    return store.all_loans()


@app.get("/loans/search")
def search_loans(q: str = "", x_user_id: str = Header(...)):
    return [
        ln for ln in store.all_loans()
        if q.lower() in ln["applicant_name"].lower()
    ]


@app.get("/loans/{loan_id}")
def get_loan(loan_id: str, x_user_id: str = Header(...)):
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    return loan


@app.patch("/loans/{loan_id}")
def update_loan(loan_id: str, body: LoanPatch, x_user_id: str = Header(...)):
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    updates = body.model_dump(exclude_none=True)
    loan.update(updates)
    store.save_loan(loan)
    return loan


@app.post("/loans/{loan_id}/clone", status_code=201)
def clone_loan(loan_id: str, x_user_id: str = Header(...)):
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    clone = dict(loan)
    clone["id"] = str(uuid.uuid4())
    clone["owner_id"] = x_user_id
    clone["status"] = "draft"
    store.save_loan(clone)
    return clone


@app.get("/loans/{loan_id}/fees")
def get_fees(loan_id: str, x_user_id: str = Header(...)):
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    return loan["fees"]


@app.get("/loans/{loan_id}/export")
def export_loan(loan_id: str, format: str = "json", x_user_id: str = Header(...)):
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "owner_id", "applicant_name", "status",
                         "underwriter_notes", "private_rate"])
        writer.writerow([
            loan["id"], loan["owner_id"], loan["applicant_name"],
            loan["status"], loan["underwriter_notes"], loan["private_rate"],
        ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return loan


@app.get("/loans/{loan_id}/documents")
def get_document(loan_id: str, name: str, x_user_id: str = Header(...)):
    parts = [p for p in name.replace("\\", "/").split("/") if p and p != ".."]
    if len(parts) >= 2:
        target_id, doc_name = parts[-2], parts[-1]
        target = store.get_loan(target_id)
        if target is None:
            raise HTTPException(status_code=404)
        content = target["documents"].get(doc_name)
        if content is None:
            raise HTTPException(status_code=404)
        return {"content": content}
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    content = loan["documents"].get(name)
    if content is None:
        raise HTTPException(status_code=404)
    return {"content": content}


@app.post("/loans/{loan_id}/submit")
def submit_loan(loan_id: str, x_user_id: str = Header(...)):
    loan = store.get_loan(loan_id)
    if loan is None:
        raise HTTPException(status_code=404)
    loan["status"] = "submitted"
    store.save_loan(loan)
    return loan
