from __future__ import annotations
import io
import json
import zipfile
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from ticketsvc import store

app = FastAPI()


class TicketIn(BaseModel):
    title: str
    description: str
    internal_notes: str = ""
    priority: str = "medium"
    assignee_id: str = ""
    attachments: dict = {}
    tags: list = []


@app.post("/tickets", status_code=201)
def create_ticket(body: TicketIn, x_user_id: str = Header(...)):
    return store.create_ticket(
        reporter_id=x_user_id,
        title=body.title,
        description=body.description,
        internal_notes=body.internal_notes,
        priority=body.priority,
        assignee_id=body.assignee_id,
        attachments=body.attachments,
        tags=body.tags,
    )


@app.get("/tickets")
def list_tickets(x_user_id: str = Header(...)):
    # BUG: no ownership filter — internal_notes visible to every caller
    return store.list_tickets()


@app.get("/tickets/search")
def search_tickets(q: str = Query(...), x_user_id: str = Header(...)):
    # BUG: searches internal_notes content, returns matches to anyone
    return store.search_tickets(q)


@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: str, x_user_id: str = Header(...)):
    t = store.get_ticket(ticket_id)
    if t is None:
        raise HTTPException(404)
    # BUG: returns internal_notes to any authenticated caller
    return t


class TicketPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    internal_notes: Optional[str] = None


@app.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: str, body: TicketPatch, x_user_id: str = Header(...)):
    updated = store.update_ticket(ticket_id, **body.model_dump())
    if updated is None:
        raise HTTPException(404)
    return updated


class CommentIn(BaseModel):
    body: str
    type: str = "public"


@app.post("/tickets/{ticket_id}/comments", status_code=201)
def add_comment(ticket_id: str, body: CommentIn, x_user_id: str = Header(...)):
    if store.get_ticket(ticket_id) is None:
        raise HTTPException(404)
    return store.add_comment(ticket_id, x_user_id, body.body, body.type)


@app.get("/tickets/{ticket_id}/comments")
def list_comments(ticket_id: str, x_user_id: str = Header(...)):
    if store.get_ticket(ticket_id) is None:
        raise HTTPException(404)
    # BUG: returns type="internal" comments to any caller, not just agents
    return store.list_comments(ticket_id)


@app.get("/tickets/{ticket_id}/attachments")
def get_attachment(ticket_id: str, name: str = Query(...),
                   x_user_id: str = Header(...)):
    if store.get_ticket(ticket_id) is None:
        raise HTTPException(404)
    # BUG: no ownership check — private attachments served to anyone
    # BUG: path traversal — names with ../ resolve to global private store
    if ".." in name:
        clean = name.replace("../", "").replace("..", "")
        content = store.get_private_global(clean)
        if content:
            return {"name": name, "content": content}
    content = store.get_attachment(ticket_id, name)
    if content is None:
        raise HTTPException(404)
    return {"name": name, "content": content}


@app.get("/tickets/{ticket_id}/export")
def export_ticket(ticket_id: str, format: str = Query("json"),
                  x_user_id: str = Header(...)):
    t = store.get_ticket(ticket_id)
    if t is None:
        raise HTTPException(404)
    comments = store.list_comments(ticket_id)
    # BUG: no role check — exports internal_notes and all comments to anyone
    if format == "zip":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("ticket.json", json.dumps(t))
            zf.writestr("comments.json", json.dumps(comments))
            for fname, content in t["attachments"].items():
                zf.writestr(f"attachments/{fname}", content)
        return Response(content=buf.getvalue(), media_type="application/zip")
    return {"ticket": t, "comments": comments}


@app.post("/tickets/{ticket_id}/clone", status_code=201)
def clone_ticket(ticket_id: str, x_user_id: str = Header(...)):
    cloned = store.clone_ticket(ticket_id, x_user_id)
    if cloned is None:
        raise HTTPException(404)
    # BUG: clone inherits internal_notes from source — laundering vector
    return cloned
