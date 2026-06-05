from __future__ import annotations
from paymentsvc.models import Payment

_store: dict[str, Payment] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    merchant: str = "Unknown",
    status: str = "pending",
    line_items: list | None = None,
    private_notes: str = "",
    reference_code: str = "",
    documents: dict | None = None,
    collaborators: list | None = None,
    visibility: str = "private",
) -> Payment:
    pmt = Payment(
        owner_id=owner_id,
        merchant=merchant,
        status=status,
        line_items=line_items or [],
        private_notes=private_notes,
        reference_code=reference_code,
        documents=documents or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _store[pmt.id] = pmt
    return pmt


def get(payment_id: str) -> Payment | None:
    return _store.get(payment_id)


def list_all() -> list[Payment]:
    return list(_store.values())


def update(payment_id: str, **kwargs) -> Payment | None:
    pmt = _store.get(payment_id)
    if pmt is None:
        return None
    data = pmt.model_dump()
    data.update(kwargs)
    updated = Payment(**data)
    _store[payment_id] = updated
    return updated
