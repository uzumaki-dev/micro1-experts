from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class DataPoint(BaseModel):
    label: str
    value: float = 0.0
    metric_code: str = ""


class ReportCreate(BaseModel):
    title: str
    status: str = "draft"
    data_points: list[DataPoint] = []
    confidential_notes: str = ""
    attachments: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class ReportPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    confidential_notes: Optional[str] = None
    collaborators: Optional[list[str]] = None
    visibility: Optional[str] = None


class Report(BaseModel):
    id: str
    owner_id: str
    title: str
    status: str
    data_points: list[DataPoint]
    confidential_notes: str
    attachments: dict[str, str]
    collaborators: list[str]
    visibility: str
