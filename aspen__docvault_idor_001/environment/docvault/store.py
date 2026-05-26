"""In-memory document store for the DocVault workspace.

Access policy (intended): a document's body, secret_notes, and attachments are
private to its owner. Admins (user id "admin") and listed collaborators may also
access them. A document with visibility "public" exposes its body to anyone, but
secret_notes and attachments stay restricted to the owner, admins, and
collaborators. Listing and search return only documents the caller may see.
"""
import posixpath
import uuid

ADMIN_ID = "admin"


class DocError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


_documents: dict = {}        # id -> document dict
_attachments: dict = {}      # normalized "/att/<id>/<name>" -> content


def reset():
    _documents.clear()
    _attachments.clear()


def _snapshot(doc: dict) -> dict:
    return {"title": doc["title"], "body": doc["body"], "secret_notes": doc["secret_notes"]}


def _att_key(doc_id: str, name: str) -> str:
    return posixpath.normpath(f"/att/{doc_id}/{name}")


def create_document(owner_id, *, title, body="", visibility="private",
                    secret_notes="", collaborators=None, attachments=None) -> dict:
    did = uuid.uuid4().hex
    doc = {
        "id": did,
        "owner_id": owner_id,
        "title": title,
        "body": body,
        "visibility": visibility,
        "secret_notes": secret_notes,
        "collaborators": list(collaborators or []),
        "attachments": dict(attachments or {}),
        "versions": [],
    }
    doc["versions"].append(_snapshot(doc))
    _documents[did] = doc
    for name, content in doc["attachments"].items():
        _attachments[_att_key(did, name)] = content
    return doc


def get_document(did: str) -> dict:
    doc = _documents.get(did)
    if doc is None:
        raise DocError(404, "document not found")
    return doc


def list_documents() -> list:
    return list(_documents.values())


def search_documents(q: str) -> list:
    q = (q or "").lower()
    out = []
    for doc in _documents.values():
        haystack = " ".join([doc["title"], doc["body"], doc["secret_notes"]]).lower()
        if q and q in haystack:
            out.append(doc)
    return out


def update_document(did: str, *, title=None, body=None, secret_notes=None) -> dict:
    doc = get_document(did)
    if title is not None:
        doc["title"] = title
    if body is not None:
        doc["body"] = body
    if secret_notes is not None:
        doc["secret_notes"] = secret_notes
    doc["versions"].append(_snapshot(doc))
    return doc


def duplicate_document(did: str, new_owner_id: str) -> dict:
    src = get_document(did)
    return create_document(
        new_owner_id,
        title=src["title"] + " (copy)",
        body=src["body"],
        visibility="private",
        secret_notes=src["secret_notes"],
        collaborators=[],
        attachments=dict(src["attachments"]),
    )


def get_attachment(did: str, name: str):
    # The name is joined to the document's attachment namespace and normalized.
    # Traversal segments in `name` are NOT rejected, so a name like
    # "../<other_id>/<file>" resolves into another document's attachments.
    return _attachments.get(_att_key(did, name))
