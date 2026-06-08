from __future__ import annotations
import csv
import io
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse

from surveysvc import store
from surveysvc.models import Survey, SurveyCreate, SurveyPatch

app = FastAPI()

ADMIN = "admin"


@app.post("/surveys", status_code=201)
def create_survey(body: SurveyCreate, x_user_id: str = Header(...)) -> Survey:
    return store.create(
        owner_id=x_user_id,
        title=body.title,
        description=body.description,
        status=body.status,
        visibility=body.visibility,
        collaborators=body.collaborators,
        internal_notes=body.internal_notes,
        responses=body.responses,
        attachments=body.attachments,
    )


@app.get("/surveys")
def list_surveys(x_user_id: str = Header(...)) -> list[Survey]:
    # BUG: returns all surveys regardless of ownership
    return store.list_all()


@app.get("/surveys/search")
def search_surveys(
    q: str = Query(""), x_user_id: str = Header(...)
) -> list[Survey]:
    # BUG: searches across all surveys regardless of ownership
    q_lower = q.lower()
    return [
        s
        for s in store.list_all()
        if q_lower in s.title.lower() or q_lower in s.internal_notes.lower()
    ]


@app.get("/surveys/{survey_id}")
def get_survey(survey_id: str, x_user_id: str = Header(...)) -> Survey:
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check — any authenticated user can read any survey
    return s


@app.get("/surveys/{survey_id}/responses")
def get_responses(survey_id: str, x_user_id: str = Header(...)):
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check, leaks score_code
    return s.responses


@app.get("/surveys/{survey_id}/export")
def export_survey(
    survey_id: str,
    format: str = Query("json"),
    x_user_id: str = Header(...),
):
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "title", "owner_id", "status", "internal_notes",
            "question_id", "answer", "score_code",
        ])
        for resp in s.responses:
            writer.writerow([
                s.id, s.title, s.owner_id, s.status, s.internal_notes,
                resp.question_id, resp.answer, resp.score_code,
            ])
        if not s.responses:
            writer.writerow([
                s.id, s.title, s.owner_id, s.status, s.internal_notes,
                "", "", "",
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    return s


@app.get("/surveys/{survey_id}/attachments")
def get_attachment(
    survey_id: str,
    name: str = Query(...),
    x_user_id: str = Header(...),
):
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check
    content = s.attachments.get(name)
    if content is None:
        # BUG: naive path traversal — discards path prefix, scans all surveys
        # for the last path component (filename-wildcard across all surveys)
        parts = name.replace("\\", "/").split("/")
        if len(parts) >= 2:
            other_file = parts[-1]
            for other_s in store.list_all():
                other_content = other_s.attachments.get(other_file)
                if other_content is not None:
                    return PlainTextResponse(other_content)
        raise HTTPException(status_code=404, detail="Attachment not found")
    return PlainTextResponse(content)


@app.patch("/surveys/{survey_id}")
def patch_survey(
    survey_id: str, body: SurveyPatch, x_user_id: str = Header(...)
) -> Survey:
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and s.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    updated = store.update(survey_id, **updates)
    return updated  # type: ignore[return-value]


@app.post("/surveys/{survey_id}/clone", status_code=201)
def clone_survey(survey_id: str, x_user_id: str = Header(...)) -> Survey:
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: inherits internal_notes, responses (with score_code), attachments verbatim
    return store.create(
        owner_id=x_user_id,
        title=s.title,
        description=s.description,
        status="draft",
        visibility="private",
        internal_notes=s.internal_notes,   # BUG: copies private notes
        responses=s.responses,              # BUG: copies responses with private score_code
        attachments=s.attachments,          # BUG: copies private attachments
    )


@app.post("/surveys/{survey_id}/publish")
def publish_survey(survey_id: str, x_user_id: str = Header(...)) -> Survey:
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    if x_user_id != ADMIN and s.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = store.update(survey_id, status="published")
    return updated  # type: ignore[return-value]


@app.post("/surveys/{survey_id}/share")
def share_survey(survey_id: str, x_user_id: str = Header(...)) -> Survey:
    s = store.get(survey_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Not found")
    # BUG: no ownership check, returns full survey including internal_notes
    return s
