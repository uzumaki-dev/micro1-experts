import sqlite3
import uuid
from datetime import datetime

conn = sqlite3.connect(":memory:", check_same_thread=False)
conn.row_factory = sqlite3.Row


def _init():
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id       TEXT PRIMARY KEY,
            owner    TEXT NOT NULL,
            title    TEXT NOT NULL,
            body     TEXT NOT NULL,
            tags     TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()


_init()


def reset():
    conn.execute("DROP TABLE IF EXISTS notes")
    conn.commit()
    _init()


def create_note(owner: str, title: str, body: str, tags: list) -> dict:
    note_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    tags_str = ",".join(tags)
    conn.execute(
        "INSERT INTO notes (id, owner, title, body, tags, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (note_id, owner, title, body, tags_str, created_at),
    )
    conn.commit()
    return _row_to_dict(
        conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    )


def get_note(note_id: str, owner: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM notes WHERE id = ? AND owner = ?", (note_id, owner)
    ).fetchone()
    return _row_to_dict(row) if row else None


def list_notes(owner: str) -> list:
    rows = conn.execute(
        "SELECT * FROM notes WHERE owner = ? ORDER BY created_at DESC", (owner,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_note(note_id: str, owner: str, **fields) -> dict | None:
    if get_note(note_id, owner) is None:
        return None
    for key, val in fields.items():
        if key == "tags":
            val = ",".join(val)
        conn.execute(f"UPDATE notes SET {key} = ? WHERE id = ?", (val, note_id))
    conn.commit()
    return get_note(note_id, owner)


def delete_note(note_id: str, owner: str) -> bool:
    result = conn.execute(
        "DELETE FROM notes WHERE id = ? AND owner = ?", (note_id, owner)
    )
    conn.commit()
    return result.rowcount > 0


# --- BUGGY query functions — raw f-string interpolation ---

def search_notes(owner: str, q: str) -> list:
    # BUG: q= not sanitized — UNION injection via closing the AND ( paren
    cursor = conn.execute(
        f"SELECT * FROM notes WHERE owner='{owner}' "
        f"AND (title LIKE '%{q}%' OR body LIKE '%{q}%')"
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def filter_by_tag(owner: str, tag: str) -> list:
    # BUG: tag= not sanitized — UNION injection collapses owner filter
    cursor = conn.execute(
        f"SELECT * FROM notes WHERE owner='{owner}' AND tags LIKE '%{tag}%'"
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def recent_notes(owner: str, days: str) -> list:
    # BUG: days= not sanitized — UNION injection via closing datetime()
    cursor = conn.execute(
        f"SELECT * FROM notes WHERE owner='{owner}' "
        f"AND created_at >= datetime('now', '-{days} days')"
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["tags"] = d["tags"].split(",") if d["tags"] else []
    return d
