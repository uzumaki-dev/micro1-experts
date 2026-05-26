from typing import Optional

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    title: str
    body: str = ""
    visibility: str = "private"  # "private" | "public"
    secret_notes: str = ""
    collaborators: list[str] = Field(default_factory=list)
    attachments: dict[str, str] = Field(default_factory=dict)  # name -> content


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    secret_notes: Optional[str] = None
