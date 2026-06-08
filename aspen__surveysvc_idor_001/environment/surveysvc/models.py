from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ResponseEntry(BaseModel):
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_id: str = ""
    answer: str = ""
    score_code: str = ""


class Survey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str = "Untitled Survey"
    description: str = ""
    status: str = "draft"
    visibility: str = "private"
    collaborators: list[str] = []
    internal_notes: str = ""
    responses: list[ResponseEntry] = []
    attachments: dict[str, str] = {}


class SurveyCreate(BaseModel):
    title: str = "Untitled Survey"
    description: str = ""
    status: str = "draft"
    visibility: str = "private"
    collaborators: list[str] = []
    internal_notes: str = ""
    responses: list[ResponseEntry] = []
    attachments: dict[str, str] = {}


class SurveyPatch(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None
    internal_notes: Optional[str] = None
