"""Quiz-bank management endpoints: create, audit, list, duplicate, rename, share, export."""

from __future__ import annotations

import base64
import copy
import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from quizhub.auth import Caller, caller
from quizhub.db import ATTEMPTS, QUIZZES, artifact_dir, new_id, resource_dir

router = APIRouter(tags=["quiz-bank"])


class CreateQuizRequest(BaseModel):
    title: str
    public_handout: str
    questions: list[str] = Field(default_factory=list)
    answer_key_b64: str = ""
    solution_pdf_b64: str = ""
    grader_notes_b64: str = ""
    hidden_resource_files: list[str] = Field(default_factory=list)
    extra_resource_files: dict[str, str] = Field(default_factory=dict)


def _require_instructor(current: Caller) -> None:
    if not current.is_instructor:
        raise HTTPException(status_code=403, detail="instructor required")


@router.post("/quiz-bank")
def create_quiz(payload: CreateQuizRequest, current: Caller = Depends(caller)):
    _require_instructor(current)

    quiz_id = new_id()
    answer_bundle = {
        "answer_key_b64": payload.answer_key_b64,
        "solution_pdf_b64": payload.solution_pdf_b64,
        "grader_notes_b64": payload.grader_notes_b64,
        "hidden_resource_files": list(payload.hidden_resource_files),
    }
    row = {
        "id": quiz_id,
        "title": payload.title,
        "questions": list(payload.questions),
        "answer_bundle": answer_bundle,
        "owner_id": current.user_id,
    }
    QUIZZES[quiz_id] = row

    quiz_root = resource_dir(quiz_id)
    with open(os.path.join(quiz_root, "public_handout.md"), "wb") as fh:
        fh.write(payload.public_handout.encode("utf-8"))

    for filename, encoded in payload.extra_resource_files.items():
        if not filename:
            continue
        with open(os.path.join(quiz_root, filename), "wb") as fh:
            fh.write(base64.b64decode(encoded.encode("utf-8"), validate=False))

    return row


@router.post("/quiz-bank/{quiz_id}/audit-answer-key")
def audit_answer_key(quiz_id: str, current: Caller = Depends(caller)):
    _require_instructor(current)

    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")

    answer_bundle = quiz.get("answer_bundle") or {}
    answer_key = base64.b64decode(
        str(answer_bundle.get("answer_key_b64", "")).encode("utf-8"),
        validate=False,
    )
    if not answer_key:
        raise HTTPException(status_code=400, detail="answer key is empty")

    key_root = os.path.join(resource_dir(quiz_id), ".key")
    os.makedirs(key_root, exist_ok=True)
    with open(os.path.join(key_root, "answer_key.txt"), "wb") as fh:
        fh.write(answer_key)

    attempt_id = new_id()
    attempt = {
        "id": attempt_id,
        "quiz_id": quiz_id,
        "mode": "answer_key_audit",
        "status": "completed",
        "created_by": current.user_id,
    }
    ATTEMPTS[attempt_id] = attempt

    attempt_root = artifact_dir(attempt_id)
    with open(os.path.join(attempt_root, "answer_key.txt"), "wb") as fh:
        fh.write(answer_key)
    with open(os.path.join(attempt_root, "audit_log.txt"), "wb") as fh:
        fh.write(b"answer-key audit completed")

    return {"attempt_id": attempt_id, "status": "completed"}


@router.get("/quiz-bank")
def list_quizzes(_current: Caller = Depends(caller)):
    """List all quizzes in the quiz bank."""
    return list(QUIZZES.values())


class DuplicateRequest(BaseModel):
    new_title: str = ""


@router.post("/quizzes/{quiz_id}/duplicate")
def duplicate_quiz(quiz_id: str, payload: DuplicateRequest, current: Caller = Depends(caller)):
    """Clone a quiz under a new id (used by students building practice sets)."""
    src = QUIZZES.get(quiz_id)
    if src is None:
        raise HTTPException(status_code=404, detail="quiz not found")

    new_quiz_id = new_id()
    cloned = copy.deepcopy(src)
    cloned["id"] = new_quiz_id
    cloned["title"] = payload.new_title or f"{src.get('title', 'quiz')}-copy"
    cloned["owner_id"] = current.user_id
    QUIZZES[new_quiz_id] = cloned
    return cloned


class PatchQuizRequest(BaseModel):
    title: str | None = None


@router.patch("/quizzes/{quiz_id}")
def patch_quiz(quiz_id: str, payload: PatchQuizRequest, _current: Caller = Depends(caller)):
    """Update mutable quiz metadata."""
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")
    if payload.title is not None:
        quiz["title"] = payload.title
    return quiz


@router.post("/quizzes/{quiz_id}/share")
def share_quiz(quiz_id: str, _current: Caller = Depends(caller)):
    """Generate a shareable link payload for a quiz."""
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")
    return {
        "quiz_id": quiz_id,
        "share_id": new_id(),
        "title": quiz.get("title"),
        "bundle": quiz.get("answer_bundle"),
        "url": f"/shared/{quiz_id}",
    }


@router.get("/quizzes/{quiz_id}/export")
def export_quiz(quiz_id: str, _current: Caller = Depends(caller)):
    """Download a JSON dump of a quiz's configuration."""
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")
    return quiz
