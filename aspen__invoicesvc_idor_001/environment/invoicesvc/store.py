from __future__ import annotations
import uuid
from invoicesvc.models import Invoice, LineItem

_invoices: dict[str, Invoice] = {}


def reset() -> None:
    _invoices.clear()


def create(
    owner_id: str,
    client_name: str,
    status: str = "draft",
    line_items: list[LineItem] | None = None,
    internal_notes: str = "",
    attachments: dict[str, str] | None = None,
    collaborators: list[str] | None = None,
    visibility: str = "private",
) -> Invoice:
    inv = Invoice(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        client_name=client_name,
        status=status,
        line_items=line_items or [],
        internal_notes=internal_notes,
        attachments=attachments or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _invoices[inv.id] = inv
    return inv


def get(invoice_id: str) -> Invoice | None:
    return _invoices.get(invoice_id)


def list_all() -> list[Invoice]:
    return list(_invoices.values())


def update(invoice_id: str, **kwargs) -> Invoice | None:
    inv = _invoices.get(invoice_id)
    if inv is None:
        return None
    updated = inv.model_copy(update={k: v for k, v in kwargs.items()})
    _invoices[invoice_id] = updated
    return updated
