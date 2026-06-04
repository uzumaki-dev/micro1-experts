from __future__ import annotations
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from contractsvc import store
from contractsvc.models import Contract, ContractCreate, ContractPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/contracts", status_code=201)
def create_contract(body: ContractCreate, x_user_id: str = Header(...)) -> Contract:
    return store.create(
        owner_id=x_user_id,
        title=body.title,
        status=body.status,
        counterparty_id=body.counterparty_id,
        clauses=body.clauses,
        internal_notes=body.internal_notes,
        documents=body.documents,
        collaborators=body.collaborators,
        visibility=body.visibility,
    )


@app.get("/contracts")
def list_contracts(x_user_id: str = Header(...)) -> list[Contract]:
    return store.list_all()


@app.get("/contracts/search")
def search_contracts(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Contract]:
    q_lower = q.lower()
    return [
        c for c in store.list_all()
        if q_lower in c.title.lower() or q_lower in c.internal_notes.lower()
    ]


@app.get("/contracts/{contract_id}")
def get_contract(contract_id: str, x_user_id: str = Header(...)) -> Contract:
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    return contract


@app.get("/contracts/{contract_id}/clauses")
def get_clauses(contract_id: str, x_user_id: str = Header(...)):
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    return contract.clauses


@app.get("/contracts/{contract_id}/export")
def export_contract(
    contract_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    if format == "pdf":
        lines = [
            f"CONTRACT: {contract.title}",
            f"STATUS: {contract.status}",
            f"COUNTERPARTY: {contract.counterparty_id}",
            f"INTERNAL_NOTES: {contract.internal_notes}",
        ]
        for clause in contract.clauses:
            lines.append(
                f"CLAUSE: {clause.description} | QTY: {clause.quantity} | RATE: {clause.rate_card}"
            )
        return PlainTextResponse("\n".join(lines), media_type="text/plain")
    return contract


@app.get("/contracts/{contract_id}/documents")
def get_document(
    contract_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    content = contract.documents.get(name)
    if content is None:
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_contract in store.list_all():
                other_content = other_contract.documents.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(content)


@app.patch("/contracts/{contract_id}")
def patch_contract(
    contract_id: str, body: ContractPatch, x_user_id: str = Header(...)
) -> Contract:
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and contract.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(contract_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/contracts/{contract_id}/duplicate", status_code=201)
def duplicate_contract(contract_id: str, x_user_id: str = Header(...)) -> Contract:
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    return store.create(
        owner_id=x_user_id,
        title=contract.title,
        status="draft",
        counterparty_id=contract.counterparty_id,
        clauses=contract.clauses,
        internal_notes=contract.internal_notes,
        documents=contract.documents,
        collaborators=[],
        visibility="private",
    )


@app.post("/contracts/{contract_id}/sign")
def sign_contract(contract_id: str, x_user_id: str = Header(...)) -> Contract:
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and contract.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(contract_id, status="signed")
    return updated  # type: ignore[return-value]


@app.post("/contracts/{contract_id}/share")
def share_contract(
    contract_id: str,
    user_id: str = Query(...),
    x_user_id: str = Header(...),
) -> Contract:
    contract = store.get(contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and contract.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    colls = list(contract.collaborators)
    if user_id not in colls:
        colls.append(user_id)
    updated = store.update(contract_id, collaborators=colls)
    return updated  # type: ignore[return-value]
