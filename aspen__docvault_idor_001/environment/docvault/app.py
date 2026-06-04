"""HTTP layer for the DocVault document workspace.

The caller is identified by the `X-User-Id` request header. See store.py for the
intended access policy. NOTE: the read/export/share/duplicate endpoints below do
not enforce that policy.
"""
import io
import uuid
import zipfile
from typing import Optional

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, Response

from docvault import store
from docvault.models import DocumentCreate, DocumentUpdate

app = FastAPI(title="DocVault")

_FIELDS = ("id", "owner_id", "title", "body", "visibility",
           "secret_notes", "collaborators", "attachments")


def _require_user(x_user_id: Optional[str]) -> str:
    if not x_user_id:
        raise store.DocError(401, "X-User-Id header is required")
    return x_user_id


def _full(doc: dict) -> dict:
    return {k: doc[k] for k in _FIELDS}


@app.exception_handler(store.DocError)
async def _doc_error_handler(request: Request, exc: store.DocError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.post("/documents", status_code=201)
def create_document(body: DocumentCreate,
                    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    uid = _require_user(x_user_id)
    doc = store.create_document(
        uid, title=body.title, body=body.body, visibility=body.visibility,
        secret_notes=body.secret_notes, collaborators=body.collaborators,
        attachments=body.attachments,
    )
    return _full(doc)


@app.get("/documents")
def list_documents(x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    return [_full(d) for d in store.list_documents()]


@app.get("/documents/search")
def search_documents(q: str = "",
                     x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    return [_full(d) for d in store.search_documents(q)]


@app.get("/documents/{doc_id}")
def get_document(doc_id: str,
                 x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    doc = store.get_document(doc_id)
    return _full(doc)


@app.patch("/documents/{doc_id}")
def update_document(doc_id: str, body: DocumentUpdate,
                    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    doc = store.update_document(doc_id, title=body.title, body=body.body,
                                secret_notes=body.secret_notes)
    return _full(doc)


@app.get("/documents/{doc_id}/export")
def export_document(doc_id: str, format: str = "json",
                    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    doc = store.get_document(doc_id)
    if format == "zip":
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("body.txt", doc["body"])
            z.writestr("secret_notes.txt", doc["secret_notes"])
            for name, content in doc["attachments"].items():
                z.writestr(f"attachments/{name}", content)
        return Response(content=buf.getvalue(), media_type="application/zip")
    return _full(doc)


@app.get("/documents/{doc_id}/versions")
def get_versions(doc_id: str,
                 x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    doc = store.get_document(doc_id)
    return {"id": doc["id"], "versions": doc["versions"]}


@app.get("/documents/{doc_id}/attachments")
def get_attachment(doc_id: str, name: str = "",
                   x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    store.get_document(doc_id)
    content = store.get_attachment(doc_id, name)
    if content is None:
        raise store.DocError(404, "attachment not found")
    return Response(content=content, media_type="text/plain")


@app.post("/documents/{doc_id}/duplicate", status_code=201)
def duplicate_document(doc_id: str,
                       x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    uid = _require_user(x_user_id)
    new = store.duplicate_document(doc_id, uid)
    return _full(new)


@app.post("/documents/{doc_id}/share")
def share_document(doc_id: str,
                   x_user_id: Optional[str] = Header(default=None, alias="X-User-Id")):
    _require_user(x_user_id)
    doc = store.get_document(doc_id)
    return {"share_id": uuid.uuid4().hex, "document": _full(doc)}
