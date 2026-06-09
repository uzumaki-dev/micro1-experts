from __future__ import annotations
import uuid
from quotesvc.models import Quote, LineItem

_quotes: dict[str, Quote] = {}


def reset() -> None:
    _quotes.clear()


def create(
    owner_id: str,
    client_name: str = "",
    status: str = "draft",
    line_items: list[LineItem] | None = None,
    internal_notes: str = "",
    terms: str = "",
    attachments: dict[str, str] | None = None,
    collaborators: list[str] | None = None,
    visibility: str = "private",
) -> Quote:
    q = Quote(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        client_name=client_name,
        status=status,
        line_items=line_items or [],
        internal_notes=internal_notes,
        terms=terms,
        attachments=attachments or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _quotes[q.id] = q
    return q


def get(quote_id: str) -> Quote | None:
    return _quotes.get(quote_id)


def list_all() -> list[Quote]:
    return list(_quotes.values())


def update(quote_id: str, **kwargs) -> Quote | None:
    q = _quotes.get(quote_id)
    if q is None:
        return None
    updated = q.model_copy(update={k: v for k, v in kwargs.items()})
    _quotes[quote_id] = updated
    return updated
