from __future__ import annotations
from contractsvc.models import Contract

_store: dict[str, Contract] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    title: str = "Untitled",
    status: str = "draft",
    counterparty_id: str = "",
    clauses: list | None = None,
    internal_notes: str = "",
    documents: dict | None = None,
    collaborators: list | None = None,
    visibility: str = "private",
) -> Contract:
    contract = Contract(
        owner_id=owner_id,
        title=title,
        status=status,
        counterparty_id=counterparty_id,
        clauses=clauses or [],
        internal_notes=internal_notes,
        documents=documents or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _store[contract.id] = contract
    return contract


def get(contract_id: str) -> Contract | None:
    return _store.get(contract_id)


def list_all() -> list[Contract]:
    return list(_store.values())


def update(contract_id: str, **kwargs) -> Contract | None:
    contract = _store.get(contract_id)
    if contract is None:
        return None
    data = contract.model_dump()
    data.update(kwargs)
    updated = Contract(**data)
    _store[contract_id] = updated
    return updated
