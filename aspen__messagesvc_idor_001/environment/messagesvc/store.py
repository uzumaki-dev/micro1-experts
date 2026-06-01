from __future__ import annotations
import uuid

_threads: dict[str, dict] = {}
_messages: dict[str, dict] = {}


def reset():
    _threads.clear()
    _messages.clear()


def create_thread(creator_id, title, participants, initial_body,
                  private_content="", attachments=None):
    tid = str(uuid.uuid4())
    _threads[tid] = {
        "id": tid,
        "title": title,
        "created_by": creator_id,
        "participants": list(participants),
        "attachments": dict(attachments or {}),
    }
    mid = str(uuid.uuid4())
    _messages[mid] = {
        "id": mid,
        "thread_id": tid,
        "sender": creator_id,
        "body": initial_body,
        "private_content": private_content,
        "parent_id": None,
    }
    return dict(_threads[tid])


def get_thread_raw(tid: str):
    t = _threads.get(tid)
    return dict(t) if t else None


def get_thread(tid: str):
    t = _threads.get(tid)
    if t is None:
        return None
    thread_messages = [m for m in _messages.values() if m["thread_id"] == tid]
    latest = dict(thread_messages[-1]) if thread_messages else None
    result = dict(t)
    result["latest_message"] = latest
    return result


def list_threads():
    result = []
    for t in _threads.values():
        thread_messages = [m for m in _messages.values() if m["thread_id"] == t["id"]]
        latest = dict(thread_messages[-1]) if thread_messages else None
        entry = dict(t)
        entry["latest_message"] = latest
        result.append(entry)
    return result


def search_messages(q: str):
    q_lower = q.lower()
    results = []
    for m in _messages.values():
        if q_lower in m["body"].lower() or q_lower in m["private_content"].lower():
            t = _threads.get(m["thread_id"])
            entry = dict(m)
            entry["thread_title"] = t["title"] if t else ""
            results.append(entry)
    return results


def list_thread_messages(thread_id: str):
    return [dict(m) for m in _messages.values() if m["thread_id"] == thread_id]


def post_message(thread_id: str, sender: str, body: str, private_content: str = ""):
    mid = str(uuid.uuid4())
    _messages[mid] = {
        "id": mid,
        "thread_id": thread_id,
        "sender": sender,
        "body": body,
        "private_content": private_content,
        "parent_id": None,
    }
    return dict(_messages[mid])


def get_message(mid: str):
    m = _messages.get(mid)
    return dict(m) if m else None


def get_attachment(thread_id: str, name: str):
    t = _threads.get(thread_id)
    if t is None:
        return None
    return t.get("attachments", {}).get(name)
