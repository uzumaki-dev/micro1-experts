from __future__ import annotations
import uuid
from timesheetsvc.models import Timesheet, TimeEntry

_timesheets: dict[str, Timesheet] = {}


def reset() -> None:
    _timesheets.clear()


def create(
    owner_id: str,
    project: str,
    status: str = "draft",
    entries: list[TimeEntry] | None = None,
    internal_notes: str = "",
    private_rate: float = 0.0,
    receipts: dict[str, str] | None = None,
    collaborators: list[str] | None = None,
    visibility: str = "private",
) -> Timesheet:
    ts = Timesheet(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        project=project,
        status=status,
        entries=entries or [],
        internal_notes=internal_notes,
        private_rate=private_rate,
        receipts=receipts or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _timesheets[ts.id] = ts
    return ts


def get(timesheet_id: str) -> Timesheet | None:
    return _timesheets.get(timesheet_id)


def list_all() -> list[Timesheet]:
    return list(_timesheets.values())


def update(timesheet_id: str, **kwargs) -> Timesheet | None:
    ts = _timesheets.get(timesheet_id)
    if ts is None:
        return None
    updated = ts.model_copy(update={k: v for k, v in kwargs.items()})
    _timesheets[timesheet_id] = updated
    return updated
