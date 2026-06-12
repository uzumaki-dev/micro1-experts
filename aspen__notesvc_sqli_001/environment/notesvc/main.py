from fastapi import FastAPI, Header, HTTPException, Query
from notesvc import db
from notesvc.models import NoteIn, NoteUpdate

app = FastAPI()


@app.post("/notes", status_code=201)
def create_note(body: NoteIn, x_user_id: str = Header(...)):
    return db.create_note(
        owner=x_user_id, title=body.title, body=body.body, tags=body.tags
    )


@app.get("/notes")
def list_notes(x_user_id: str = Header(...)):
    return db.list_notes(owner=x_user_id)


@app.get("/notes/search")
def search_notes(q: str = Query(...), x_user_id: str = Header(...)):
    # BUG: q passed directly into raw SQL in db.search_notes
    return db.search_notes(owner=x_user_id, q=q)


@app.get("/notes/filter")
def filter_notes(tag: str = Query(...), x_user_id: str = Header(...)):
    # BUG: tag passed directly into raw SQL in db.filter_by_tag
    return db.filter_by_tag(owner=x_user_id, tag=tag)


@app.get("/notes/recent")
def recent_notes(days: str = Query("7"), x_user_id: str = Header(...)):
    # BUG: days passed directly into raw SQL in db.recent_notes
    return db.recent_notes(owner=x_user_id, days=days)


@app.get("/notes/{note_id}")
def get_note(note_id: str, x_user_id: str = Header(...)):
    note = db.get_note(note_id=note_id, owner=x_user_id)
    if note is None:
        raise HTTPException(404)
    return note


@app.put("/notes/{note_id}")
def update_note(note_id: str, body: NoteUpdate, x_user_id: str = Header(...)):
    fields = body.model_dump(exclude_none=True)
    updated = db.update_note(note_id=note_id, owner=x_user_id, **fields)
    if updated is None:
        raise HTTPException(404)
    return updated


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: str, x_user_id: str = Header(...)):
    if not db.delete_note(note_id=note_id, owner=x_user_id):
        raise HTTPException(404)
