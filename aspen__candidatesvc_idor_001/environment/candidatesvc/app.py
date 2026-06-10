from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from candidatesvc import store
from candidatesvc.models import Candidate, CandidateCreate, CandidatePatch

app = FastAPI()

ADMIN = "admin"


def _is_privileged(user_id: str) -> bool:
    return user_id == ADMIN or user_id.startswith("recruiter")


@app.post("/candidates", status_code=201)
def create_candidate(body: CandidateCreate, x_user_id: str = Header(...)) -> Candidate:
    return store.create(
        owner_id=x_user_id,
        name=body.name,
        position=body.position,
        status=body.status,
        screening_notes=body.screening_notes,
        assessments=body.assessments,
        documents=body.documents,
        interviewer_ids=body.interviewer_ids,
        visibility=body.visibility,
    )


@app.get("/candidates")
def list_candidates(x_user_id: str = Header(...)) -> list[Candidate]:
    return store.list_all()


@app.get("/candidates/search")
def search_candidates(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Candidate]:
    q_lower = q.lower()
    return [
        c
        for c in store.list_all()
        if q_lower in c.name.lower() or q_lower in c.screening_notes.lower()
    ]


@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str, x_user_id: str = Header(...)) -> Candidate:
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    return c


@app.get("/candidates/{candidate_id}/assessments")
def get_assessments(candidate_id: str, x_user_id: str = Header(...)):
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    return c.assessments


@app.get("/candidates/{candidate_id}/export")
def export_candidate(
    candidate_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "name", "position", "status", "screening_notes",
            "round", "score", "eval_code",
        ])
        for assessment in c.assessments:
            writer.writerow([
                c.id, c.name, c.position, c.status, c.screening_notes,
                assessment.round, assessment.score, assessment.eval_code,
            ])
        if not c.assessments:
            writer.writerow([c.id, c.name, c.position, c.status, c.screening_notes,
                             "", "", ""])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return c


@app.get("/candidates/{candidate_id}/documents")
def get_document(
    candidate_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    content = c.documents.get(name)
    if content is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return PlainTextResponse(content)


@app.patch("/candidates/{candidate_id}")
def patch_candidate(
    candidate_id: str, body: CandidatePatch, x_user_id: str = Header(...)
) -> Candidate:
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    if not _is_privileged(x_user_id) and c.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(candidate_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/candidates/{candidate_id}/clone", status_code=201)
def clone_candidate(candidate_id: str, x_user_id: str = Header(...)) -> Candidate:
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    return store.create(
        owner_id=x_user_id,
        name=c.name,
        position=c.position,
        status="pending",
        screening_notes=c.screening_notes,
        assessments=c.assessments,
        documents=c.documents,
        interviewer_ids=[],
        visibility="private",
    )


@app.post("/candidates/{candidate_id}/share")
def share_candidate(candidate_id: str, x_user_id: str = Header(...)) -> Candidate:
    c = store.get(candidate_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Not found")
    if not _is_privileged(x_user_id) and c.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(candidate_id, visibility="public")
    return updated  # type: ignore[return-value]
