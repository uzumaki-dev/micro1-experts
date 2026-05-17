"""Read endpoints for quizzes: get quiz row, download resource file, download key file."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Response

from quizhub.auth import caller
from quizhub.db import QUIZZES, resource_dir

router = APIRouter(tags=["quizzes"])


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: str, _current=Depends(caller)):
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")
    return quiz


@router.get("/quizzes/{quiz_id}/resources/{filename:path}")
def get_quiz_resource(quiz_id: str, filename: str, _current=Depends(caller)):
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")

    path = os.path.join(resource_dir(quiz_id), filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="file not found")
    return Response(content=_read_bytes(path), media_type="application/octet-stream")


@router.get("/quizzes/{quiz_id}/key-file/{filename:path}")
def get_quiz_key_file(quiz_id: str, filename: str, _current=Depends(caller)):
    quiz = QUIZZES.get(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="quiz not found")

    path = os.path.join(resource_dir(quiz_id), ".key", filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="file not found")
    return Response(content=_read_bytes(path), media_type="application/octet-stream")
