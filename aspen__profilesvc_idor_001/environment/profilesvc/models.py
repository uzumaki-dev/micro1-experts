from __future__ import annotations
from pydantic import BaseModel, Field
import uuid


class ExperienceEntry(BaseModel):
    title: str
    company: str
    years: float = 0.0
    salary_band: str = ""


class ProfileCreate(BaseModel):
    display_name: str
    headline: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    private_summary: str = ""
    documents: dict[str, str] = Field(default_factory=dict)
    collaborators: list[str] = Field(default_factory=list)
    visibility: str = "private"


class ProfilePatch(BaseModel):
    display_name: str | None = None
    headline: str | None = None
    skills: list[str] | None = None
    visibility: str | None = None


class Profile(ProfileCreate):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    owner_id: str = ""
