"""Smoke tests for notesvc — encode normal-operation surface only.

These tests describe legitimate expected behavior and MUST PASS against
the shipped (vulnerable) substrate. They do NOT probe the SQLi bug.
"""
import pytest
from fastapi.testclient import TestClient
from notesvc.main import app
import notesvc.db as db


@pytest.fixture(autouse=True)
def _reset():
    db.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id):
    return {"X-User-Id": user_id}


def test_create_note(client):
    r = client.post(
        "/notes",
        json={"title": "Hello", "body": "World", "tags": ["dev"]},
        headers=_h("alice"),
    )
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Hello"
    assert data["owner"] == "alice"
    assert "dev" in data["tags"]


def test_list_own_notes(client):
    client.post("/notes", json={"title": "My note", "body": "content"}, headers=_h("alice"))
    r = client.get("/notes", headers=_h("alice"))
    assert r.status_code == 200
    assert any(n["title"] == "My note" for n in r.json())


def test_list_does_not_cross_users(client):
    client.post("/notes", json={"title": "Alice note", "body": "B"}, headers=_h("alice"))
    client.post("/notes", json={"title": "Bob note", "body": "B"}, headers=_h("bob"))
    r = client.get("/notes", headers=_h("alice"))
    titles = [n["title"] for n in r.json()]
    assert "Alice note" in titles
    assert "Bob note" not in titles


def test_get_own_note(client):
    note = client.post("/notes", json={"title": "T", "body": "B"}, headers=_h("alice")).json()
    r = client.get(f"/notes/{note['id']}", headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["title"] == "T"


def test_get_other_user_note_returns_404(client):
    note = client.post("/notes", json={"title": "Private", "body": "B"}, headers=_h("alice")).json()
    r = client.get(f"/notes/{note['id']}", headers=_h("bob"))
    assert r.status_code == 404


def test_search_own_notes(client):
    client.post(
        "/notes",
        json={"title": "python tips", "body": "use comprehensions"},
        headers=_h("alice"),
    )
    r = client.get("/notes/search", params={"q": "python"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any("python" in n["title"] for n in r.json())


def test_filter_by_tag(client):
    client.post("/notes", json={"title": "T", "body": "B", "tags": ["work"]}, headers=_h("alice"))
    r = client.get("/notes/filter", params={"tag": "work"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any("work" in n["tags"] for n in r.json())


def test_recent_notes(client):
    client.post("/notes", json={"title": "Recent", "body": "Just now"}, headers=_h("alice"))
    r = client.get("/notes/recent", params={"days": "7"}, headers=_h("alice"))
    assert r.status_code == 200
    assert any(n["title"] == "Recent" for n in r.json())


def test_update_note(client):
    note = client.post("/notes", json={"title": "Old", "body": "B"}, headers=_h("alice")).json()
    r = client.put(f"/notes/{note['id']}", json={"title": "New"}, headers=_h("alice"))
    assert r.status_code == 200
    assert r.json()["title"] == "New"


def test_delete_note(client):
    note = client.post("/notes", json={"title": "T", "body": "B"}, headers=_h("alice")).json()
    r = client.delete(f"/notes/{note['id']}", headers=_h("alice"))
    assert r.status_code == 204
