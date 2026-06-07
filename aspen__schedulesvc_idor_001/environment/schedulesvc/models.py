from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ShiftEntry(BaseModel):
    shift_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str = ""
    hours: float = 0.0
    rate_code: str = ""


class Schedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str = "Untitled Schedule"
    status: str = "draft"
    visibility: str = "private"
    internal_notes: str = ""
    pay_rate: float = 0.0
    entries: list[ShiftEntry] = []
    attachments: dict[str, str] = {}


class ScheduleCreate(BaseModel):
    title: str = "Untitled Schedule"
    status: str = "draft"
    visibility: str = "private"
    internal_notes: str = ""
    pay_rate: float = 0.0
    entries: list[ShiftEntry] = []
    attachments: dict[str, str] = {}


class SchedulePatch(BaseModel):
    title: Optional[str] = None
    visibility: Optional[str] = None
    internal_notes: Optional[str] = None
    pay_rate: Optional[float] = None
