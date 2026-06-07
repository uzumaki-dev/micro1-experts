from __future__ import annotations
from schedulesvc.models import Schedule

_store: dict[str, Schedule] = {}


def reset() -> None:
    _store.clear()


def create(
    owner_id: str,
    title: str = "Untitled Schedule",
    status: str = "draft",
    visibility: str = "private",
    internal_notes: str = "",
    pay_rate: float = 0.0,
    entries: list | None = None,
    attachments: dict | None = None,
) -> Schedule:
    s = Schedule(
        owner_id=owner_id,
        title=title,
        status=status,
        visibility=visibility,
        internal_notes=internal_notes,
        pay_rate=pay_rate,
        entries=entries or [],
        attachments=attachments or {},
    )
    _store[s.id] = s
    return s


def get(schedule_id: str) -> Schedule | None:
    return _store.get(schedule_id)


def list_all() -> list[Schedule]:
    return list(_store.values())


def update(schedule_id: str, **kwargs) -> Schedule | None:
    s = _store.get(schedule_id)
    if s is None:
        return None
    data = s.model_dump()
    data.update(kwargs)
    updated = Schedule(**data)
    _store[schedule_id] = updated
    return updated
