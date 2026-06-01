from __future__ import annotations
import io
import json
import zipfile
from typing import List

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from messagesvc import store

app = FastAPI()


def _is_admin(user_id: str) -> bool:
    return user_id == "admin" or user_id.startswith("admin")


class ThreadIn(BaseModel):
    title: str
    participants: List[str]
    initial_body: str
    private_content: str = ""
    attachments: dict = {}


@app.post("/threads", status_code=201)
def create_thread(body: ThreadIn, x_user_id: str = Header(...)):
    participants = list(body.participants)
    if x_user_id not in participants:
        participants = [x_user_id] + participants
    return store.create_thread(
        creator_id=x_user_id,
        title=body.title,
        participants=participants,
        initial_body=body.initial_body,
        private_content=body.private_content,
        attachments=body.attachments,
    )


@app.get("/threads")
def list_threads(x_user_id: str = Header(...)):
    # BUG: no membership filter — private_content visible to every caller
    return store.list_threads()


@app.get("/threads/search")
def search_threads(q: str = Query(...), x_user_id: str = Header(...)):
    # BUG: searches private_content, returns results to any authenticated caller
    return store.search_messages(q)


@app.get("/threads/{thread_id}")
def get_thread(thread_id: str, x_user_id: str = Header(...)):
    t = store.get_thread(thread_id)
    if t is None:
        raise HTTPException(404)
    # BUG: no membership check — returns full thread with private_content to anyone
    return t


class MessageIn(BaseModel):
    body: str
    private_content: str = ""


@app.post("/threads/{thread_id}/messages", status_code=201)
def post_message(thread_id: str, body: MessageIn, x_user_id: str = Header(...)):
    t = store.get_thread_raw(thread_id)
    if t is None:
        raise HTTPException(404)
    # Access control correctly enforced on writes only
    if not _is_admin(x_user_id) and x_user_id not in t["participants"]:
        raise HTTPException(403)
    return store.post_message(
        thread_id=thread_id,
        sender=x_user_id,
        body=body.body,
        private_content=body.private_content,
    )


@app.get("/threads/{thread_id}/messages")
def list_messages(thread_id: str, x_user_id: str = Header(...)):
    if store.get_thread_raw(thread_id) is None:
        raise HTTPException(404)
    # BUG: no membership check — all messages with private_content returned
    return store.list_thread_messages(thread_id)


@app.get("/threads/{thread_id}/attachments")
def get_attachment(thread_id: str, name: str = Query(...),
                   x_user_id: str = Header(...)):
    if store.get_thread_raw(thread_id) is None:
        raise HTTPException(404)
    # BUG: no membership check — private attachments served to any caller
    content = store.get_attachment(thread_id, name)
    if content is None:
        raise HTTPException(404)
    return {"name": name, "content": content}


@app.get("/threads/{thread_id}/export")
def export_thread(thread_id: str, format: str = Query("json"),
                  x_user_id: str = Header(...)):
    t = store.get_thread(thread_id)
    if t is None:
        raise HTTPException(404)
    messages = store.list_thread_messages(thread_id)
    # BUG: no membership check — exports private_content and attachments to anyone
    if format == "zip":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("thread.json", json.dumps(t))
            zf.writestr("messages.json", json.dumps(messages))
            raw = store.get_thread_raw(thread_id)
            if raw:
                for fname, content in raw.get("attachments", {}).items():
                    zf.writestr(f"attachments/{fname}", content)
        return Response(content=buf.getvalue(), media_type="application/zip")
    return {"thread": t, "messages": messages}


@app.get("/messages/{message_id}")
def get_message(message_id: str, x_user_id: str = Header(...)):
    m = store.get_message(message_id)
    if m is None:
        raise HTTPException(404)
    # BUG: no membership check — any caller can read any message by ID
    return m
