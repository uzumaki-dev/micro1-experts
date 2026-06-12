from pydantic import BaseModel


class NoteIn(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
