from __future__ import annotations
import uuid
from reportsvc.models import Report, DataPoint

_reports: dict[str, Report] = {}


def reset() -> None:
    _reports.clear()


def create(
    owner_id: str,
    title: str,
    status: str = "draft",
    data_points: list[DataPoint] | None = None,
    confidential_notes: str = "",
    attachments: dict[str, str] | None = None,
    collaborators: list[str] | None = None,
    visibility: str = "private",
) -> Report:
    rpt = Report(
        id=str(uuid.uuid4()),
        owner_id=owner_id,
        title=title,
        status=status,
        data_points=data_points or [],
        confidential_notes=confidential_notes,
        attachments=attachments or {},
        collaborators=collaborators or [],
        visibility=visibility,
    )
    _reports[rpt.id] = rpt
    return rpt


def get(report_id: str) -> Report | None:
    return _reports.get(report_id)


def list_all() -> list[Report]:
    return list(_reports.values())


def update(report_id: str, **kwargs) -> Report | None:
    rpt = _reports.get(report_id)
    if rpt is None:
        return None
    updated = rpt.model_copy(update={k: v for k, v in kwargs.items()})
    _reports[report_id] = updated
    return updated
