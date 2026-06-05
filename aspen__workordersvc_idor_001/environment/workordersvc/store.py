from __future__ import annotations
from workordersvc.models import WorkOrder

_store: dict[str, WorkOrder] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    title: str = "Untitled",
    status: str = "open",
    entries: list | None = None,
    internal_notes: str = "",
    private_rate: float = 0.0,
    documents: dict | None = None,
    collaborators: list | None = None,
    visibility: str = "private",
) -> WorkOrder:
    wo = WorkOrder(
        owner_id=owner_id,
        title=title,
        status=status,
        entries=entries or [],
        internal_notes=internal_notes,
        private_rate=private_rate,
        documents=documents or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _store[wo.id] = wo
    return wo


def get(workorder_id: str) -> WorkOrder | None:
    return _store.get(workorder_id)


def list_all() -> list[WorkOrder]:
    return list(_store.values())


def update(workorder_id: str, **kwargs) -> WorkOrder | None:
    wo = _store.get(workorder_id)
    if wo is None:
        return None
    data = wo.model_dump()
    data.update(kwargs)
    updated = WorkOrder(**data)
    _store[workorder_id] = updated
    return updated
