from __future__ import annotations


def _minimal_quiz_payload():
    return {
        "title": "demo quiz",
        "public_handout": "read this before you start",
        "questions": ["what is 2 + 2?"],
        "answer_key_b64": "",
        "solution_pdf_b64": "",
        "grader_notes_b64": "",
        "hidden_resource_files": [],
        "extra_resource_files": {},
    }


def test_health(client):
    resp = client.get("/quizzes/does-not-exist")
    assert resp.status_code != 500


def test_instructor_creates_quiz(client, auth_instructor):
    resp = client.post("/quiz-bank", headers=auth_instructor, json=_minimal_quiz_payload())
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"]


def test_student_starts_an_attempt(client, auth_instructor, auth_student):
    quiz = client.post("/quiz-bank", headers=auth_instructor, json=_minimal_quiz_payload()).json()
    resp = client.post(
        "/attempts",
        headers=auth_student,
        json={"quiz_id": quiz["id"], "mode": "practice"},
    )
    assert resp.status_code == 200, resp.text


def test_student_duplicates_a_quiz(client, auth_instructor, auth_student):
    """Students legitimately duplicate quizzes into their own practice library."""
    quiz = client.post("/quiz-bank", headers=auth_instructor, json=_minimal_quiz_payload()).json()
    resp = client.post(
        f"/quizzes/{quiz['id']}/duplicate",
        headers=auth_student,
        json={"new_title": "alice-practice"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] != quiz["id"]


def test_student_shares_their_own_copy(client, auth_instructor, auth_student):
    """Students share their own practice copies with a study group."""
    quiz = client.post("/quiz-bank", headers=auth_instructor, json=_minimal_quiz_payload()).json()
    copy = client.post(f"/quizzes/{quiz['id']}/duplicate", headers=auth_student, json={}).json()
    resp = client.post(f"/quizzes/{copy['id']}/share", headers=auth_student)
    assert resp.status_code == 200, resp.text


def test_student_exports_their_own_copy(client, auth_instructor, auth_student):
    """Students export their own practice copies for offline review."""
    quiz = client.post("/quiz-bank", headers=auth_instructor, json=_minimal_quiz_payload()).json()
    copy = client.post(f"/quizzes/{quiz['id']}/duplicate", headers=auth_student, json={}).json()
    resp = client.get(f"/quizzes/{copy['id']}/export", headers=auth_student)
    assert resp.status_code == 200, resp.text


def test_student_renames_their_own_copy(client, auth_instructor, auth_student):
    """Students rename their own practice copies."""
    quiz = client.post("/quiz-bank", headers=auth_instructor, json=_minimal_quiz_payload()).json()
    copy = client.post(f"/quizzes/{quiz['id']}/duplicate", headers=auth_student, json={}).json()
    resp = client.patch(f"/quizzes/{copy['id']}", headers=auth_student, json={"title": "renamed"})
    assert resp.status_code == 200, resp.text
