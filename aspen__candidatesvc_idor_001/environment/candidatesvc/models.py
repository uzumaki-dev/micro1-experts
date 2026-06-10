from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class Assessment(BaseModel):
    round: str
    score: int = 0
    eval_code: str = ""


class CandidateCreate(BaseModel):
    name: str
    position: str = ""
    status: str = "pending"
    screening_notes: str = ""
    assessments: list[Assessment] = []
    documents: dict[str, str] = {}
    interviewer_ids: list[str] = []
    visibility: str = "private"


class CandidatePatch(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    screening_notes: Optional[str] = None
    interviewer_ids: Optional[list[str]] = None
    visibility: Optional[str] = None


class Candidate(BaseModel):
    id: str
    owner_id: str
    name: str
    position: str
    status: str
    screening_notes: str
    assessments: list[Assessment]
    documents: dict[str, str]
    interviewer_ids: list[str]
    visibility: str
