"""Smoke tests for messagesvc — encode normal-operation surface only.

These tests describe legitimate expected behavior and MUST PASS against
the shipped (vulnerable) substrate. They do NOT probe the IDOR bug.
"""
import pytest
from fastapi.testclient import TestClient

from messagesvc.app import app
from messagesvc import store


@pytest.fixture(autouse=True)
def _reset():
    store.reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def _h(user_id):
    return {"X-User-Id": user_id}


def test_participant_creates_thread(client):
    r = client.post("/threads", json={
        "title": "Project sync",
        "participants": ["alice", "bob"],
        "initial_body": "Let's coordinate on the Q3 plan.",
        "private_content": "Alice's confidential note.",
        "attachments": {"agenda.txt": "Q3 goals"},
    }, headers=_h("alice"))
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Project sync"
    assert "alice" in data["participants"]
    assert "bob" in data["participants"]


def test_participant_posts_message(client):
    t = client.post("/threads", json={
        "title": "T", "participants": ["alice", "bob"],
        "initial_body": "Hello", "private_content": "",
    }, headers=_h("alice")).json()
    r = client.post(f"/threads/{t['id']}/messages", json={
        "body": "Follow up", "private_content": "Sensitive follow-up note.",
    }, headers=_h("bob"))
    assert r.status_code == 201
    assert r.json()["sender"] == "bob"


def test_non_participant_cannot_post(client):
    t = client.post("/threads", json={
        "title": "T", "participants": ["alice", "bob"],
        "initial_body": "Hello", "private_content": "",
    }, headers=_h("alice")).json()
    r = client.post(f"/threads/{t['id']}/messages", json={
        "body": "Intruder message", "private_content": "",
    }, headers=_h("carol"))
    assert r.status_code == 403


def test_admin_reads_any_thread(client):
    t = client.post("/threads", json={
        "title": "Secret", "participants": ["alice", "bob"],
        "initial_body": "Confidential", "private_content": "TOP-SECRET",
    }, headers=_h("alice")).json()
    r = client.get(f"/threads/{t['id']}", headers=_h("admin"))
    assert r.status_code == 200
    assert r.json()["title"] == "Secret"


def test_participant_reads_thread_messages(client):
    t = client.post("/threads", json={
        "title": "T", "participants": ["alice", "bob"],
        "initial_body": "Opening", "private_content": "alice-private",
    }, headers=_h("alice")).json()
    r = client.get(f"/threads/{t['id']}/messages", headers=_h("bob"))
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) > 0


def test_participant_downloads_attachment(client):
    t = client.post("/threads", json={
        "title": "T", "participants": ["alice", "bob"],
        "initial_body": "See attached", "private_content": "",
        "attachments": {"secret.txt": "sensitive-bytes"},
    }, headers=_h("alice")).json()
    r = client.get(f"/threads/{t['id']}/attachments",
                   params={"name": "secret.txt"}, headers=_h("bob"))
    assert r.status_code == 200
    assert "sensitive-bytes" in r.text


def test_participant_exports_thread_json(client):
    t = client.post("/threads", json={
        "title": "T", "participants": ["alice", "bob"],
        "initial_body": "Opening", "private_content": "",
    }, headers=_h("alice")).json()
    r = client.get(f"/threads/{t['id']}/export",
                   params={"format": "json"}, headers=_h("alice"))
    assert r.status_code == 200
    assert "thread" in r.json()


def test_list_returns_created_thread(client):
    client.post("/threads", json={
        "title": "Visible thread", "participants": ["alice", "bob"],
        "initial_body": "Hello", "private_content": "",
    }, headers=_h("alice"))
    r = client.get("/threads", headers=_h("alice"))
    assert r.status_code == 200
    assert any(t["title"] == "Visible thread" for t in r.json())


def test_search_finds_matching_message(client):
    client.post("/threads", json={
        "title": "Planning", "participants": ["alice", "bob"],
        "initial_body": "quarterly roadmap discussion", "private_content": "",
    }, headers=_h("alice"))
    r = client.get("/threads/search", params={"q": "quarterly"}, headers=_h("alice"))
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_admin_can_post_to_any_thread(client):
    t = client.post("/threads", json={
        "title": "T", "participants": ["alice", "bob"],
        "initial_body": "Hello", "private_content": "",
    }, headers=_h("alice")).json()
    r = client.post(f"/threads/{t['id']}/messages", json={
        "body": "Admin note", "private_content": "admin-annotation",
    }, headers=_h("admin"))
    assert r.status_code == 201


