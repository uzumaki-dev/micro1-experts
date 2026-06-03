from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class TimeEntry(BaseModel):
    description: str
    hours: float = 0.0
    rate_code: str = ""
    discount_code: str = ""


class TimesheetCreate(BaseModel):
    project: str
    status: str = "draft"
    entries: list[TimeEntry] = []
    internal_notes: str = ""
    private_rate: float = 0.0
    receipts: dict[str, str] = {}
    collaborators: list[str] = []
    visibility: str = "private"


class TimesheetPatch(BaseModel):
    project: Optional[str] = None
    status: Optional[str] = None
    internal_notes: Optional[str] = None
    collaborators: Optional[list[str]] = None
    visibility: Optional[str] = None


class Timesheet(BaseModel):
    id: str
    owner_id: str
    project: str
    status: str
    entries: list[TimeEntry]
    internal_notes: str
    private_rate: float
    receipts: dict[str, str]
    collaborators: list[str]
    visibility: str
