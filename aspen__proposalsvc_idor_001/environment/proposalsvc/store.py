from __future__ import annotations
from proposalsvc.models import Proposal

_store: dict[str, Proposal] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    client_name: str = "Unnamed Client",
    status: str = "draft",
    line_items: list | None = None,
    internal_notes: str = "",
    discount_pct: float = 0.0,
    attachments: dict | None = None,
    collaborators: list | None = None,
    visibility: str = "private",
) -> Proposal:
    p = Proposal(
        owner_id=owner_id,
        client_name=client_name,
        status=status,
        line_items=line_items or [],
        internal_notes=internal_notes,
        discount_pct=discount_pct,
        attachments=attachments or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _store[p.id] = p
    return p


def get(proposal_id: str) -> Proposal | None:
    return _store.get(proposal_id)


def list_all() -> list[Proposal]:
    return list(_store.values())


def update(proposal_id: str, **kwargs) -> Proposal | None:
    p = _store.get(proposal_id)
    if p is None:
        return None
    data = p.model_dump()
    data.update(kwargs)
    updated = Proposal(**data)
    _store[proposal_id] = updated
    return updated
