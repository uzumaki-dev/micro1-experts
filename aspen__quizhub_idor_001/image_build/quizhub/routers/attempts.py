"""Attempt management endpoints: create attempts, download artifacts, list per-quiz attempts."""

from __future__ import annotations

import io
import os
import zipfile

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from quizhub.auth import caller
from quizhub.db import ATTEMPTS, QUIZZES, artifact_dir, new_id

router = APIRouter(tags=["attempts"])


class CreateAttemptRequest(BaseModel):
    quiz_id: str
    mode: str


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


@router.post("/attempts")
def create_attempt(payload: CreateAttemptRequest, current=Depends(caller)):
    if payload.quiz_id not in QUIZZES:
        raise HTTPException(status_code=404, detail="quiz not found")

    attempt_id = new_id()
    attempt = {
        "id": attempt_id,
        "quiz_id": payload.quiz_id,
        "mode": payload.mode,
        "status": "completed",
        "created_by": current.user_id,
    }
    ATTEMPTS[attempt_id] = attempt

    attempt_root = artifact_dir(attempt_id)
    with open(os.path.join(attempt_root, "submission.txt"), "wb") as fh:
        fh.write(b"student submission recorded")

    return attempt


@router.get("/attempts/{attempt_id}/artifacts/{filename:path}")
def get_attempt_artifact(attempt_id: str, filename: str, _current=Depends(caller)):
    attempt = ATTEMPTS.get(attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="attempt not found")

    path = os.path.join(artifact_dir(attempt_id), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="artifact not found")
    return Response(content=_read_bytes(path), media_type="application/octet-stream")


@router.get("/attempts/{attempt_id}/artifacts-zip")
def get_attempt_artifacts_zip(attempt_id: str, _current=Depends(caller)):
    attempt = ATTEMPTS.get(attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="attempt not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        root = artifact_dir(attempt_id)
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if os.path.isfile(path):
                zf.writestr(name, _read_bytes(path))
    return Response(content=buf.getvalue(), media_type="application/zip")


@router.get("/quizzes/{quiz_id}/attempts")
def list_attempts_for_quiz(quiz_id: str, _current=Depends(caller)):
    """List all attempts for a quiz."""
    if quiz_id not in QUIZZES:
        raise HTTPException(status_code=404, detail="quiz not found")
    return [a for a in ATTEMPTS.values() if a.get("quiz_id") == quiz_id]
