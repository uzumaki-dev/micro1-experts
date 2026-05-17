"""Bearer-token auth for quizhub.

Three static API keys are recognized:
    "instructor-key" -> Caller(role="instructor", user_id="instructor-uuid")  # quiz authors
    "student-key"    -> Caller(role="student",    user_id="alice-uuid")       # student alice
    "student2-key"   -> Caller(role="student",    user_id="bob-uuid")         # student bob
Any other token raises 401.

`Caller.is_instructor` flags quiz authors. `Caller.user_id` identifies the
calling student.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

VALID_TOKENS: dict[str, tuple[str, str]] = {
    "instructor-key": ("instructor", "instructor-uuid"),
    "student-key": ("student", "alice-uuid"),
    "student2-key": ("student", "bob-uuid"),
}


@dataclass(frozen=True)
class Caller:
    role: str
    user_id: str

    @property
    def is_instructor(self) -> bool:
        return self.role == "instructor"


def caller(authorization: str | None = Header(default=None)) -> Caller:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")
    token = authorization[len("Bearer ") :]
    entry = VALID_TOKENS.get(token)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    role, user_id = entry
    return Caller(role=role, user_id=user_id)
