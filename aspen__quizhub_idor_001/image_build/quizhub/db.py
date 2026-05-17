"""In-memory storage for the quizhub demo service.

A production assessment platform would use Postgres + cloud blob storage. For
the sample task we keep the storage shape (`quizzes`, `attempts`, resource
files on disk) but back it with in-process dicts + a temp directory, so the
service runs inside a small Docker image with no external dependencies.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from typing import Any

QUIZZES: dict[str, dict[str, Any]] = {}
ATTEMPTS: dict[str, dict[str, Any]] = {}
RESOURCE_ROOT: str = ""
ARTIFACT_ROOT: str = ""


def reset_state() -> None:
    """Wipe and re-create all storage. Called at app startup and from tests."""
    global RESOURCE_ROOT, ARTIFACT_ROOT
    QUIZZES.clear()
    ATTEMPTS.clear()
    if RESOURCE_ROOT and os.path.isdir(RESOURCE_ROOT):
        shutil.rmtree(RESOURCE_ROOT, ignore_errors=True)
    if ARTIFACT_ROOT and os.path.isdir(ARTIFACT_ROOT):
        shutil.rmtree(ARTIFACT_ROOT, ignore_errors=True)
    RESOURCE_ROOT = tempfile.mkdtemp(prefix="quizhub-resources-")
    ARTIFACT_ROOT = tempfile.mkdtemp(prefix="quizhub-artifacts-")


def new_id() -> str:
    return uuid.uuid4().hex


def resource_dir(quiz_id: str) -> str:
    path = os.path.join(RESOURCE_ROOT, quiz_id)
    os.makedirs(path, exist_ok=True)
    return path


def artifact_dir(attempt_id: str) -> str:
    path = os.path.join(ARTIFACT_ROOT, attempt_id)
    os.makedirs(path, exist_ok=True)
    return path
