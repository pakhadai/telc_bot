"""
storage.py — SQLite (міні БД), кілька сертифікатів на користувача.

Міграція: якщо таблиці порожні й існує старий users_data.json — дані імпортуються один раз.
На Railway змонтуй volume і задай SQLITE_PATH=/data/telc.sqlite (каталог /data має існувати в образі).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_FILE, SQLITE_PATH

logger = logging.getLogger(__name__)

MAX_CERTS = 5

_db_ready = False


def _connect() -> sqlite3.Connection:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            lang TEXT NOT NULL DEFAULT 'ua'
        );

        CREATE TABLE IF NOT EXISTS certs (
            chat_id TEXT NOT NULL,
            id INTEGER NOT NULL,
            label TEXT NOT NULL,
            pnr TEXT NOT NULL,
            center_date TEXT NOT NULL,
            birth TEXT NOT NULL,
            added_at TEXT NOT NULL,
            last_status TEXT NOT NULL DEFAULT 'not_found',
            last_check TEXT,
            PRIMARY KEY (chat_id, id),
            FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_certs_chat ON certs(chat_id);
        """
    )


def _migrate_json_if_needed(conn: sqlite3.Connection) -> None:
    n = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if n > 0:
        return
    legacy = Path(DATA_FILE)
    if not legacy.is_file():
        return
    try:
        with open(legacy, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Legacy JSON present but unreadable (%s), skip migration", exc)
        return
    if not isinstance(data, dict) or not data:
        return
    logger.info("Migrating %d user(s) from %s to SQLite", len(data), legacy)
    for cid, u in data.items():
        if not isinstance(u, dict):
            continue
        lang = u.get("lang", "ua")
        conn.execute(
            "INSERT OR REPLACE INTO users (chat_id, lang) VALUES (?, ?)",
            (str(cid), str(lang)),
        )
        for c in u.get("certs") or []:
            if not isinstance(c, dict):
                continue
            conn.execute(
                """
                INSERT OR REPLACE INTO certs (
                    chat_id, id, label, pnr, center_date, birth,
                    added_at, last_status, last_check
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(cid),
                    int(c["id"]),
                    str(c.get("label", "")),
                    str(c.get("pnr", "")),
                    str(c.get("center_date", "")),
                    str(c.get("birth", "")),
                    str(c.get("added_at", datetime.now().isoformat())),
                    str(c.get("last_status", "not_found")),
                    c.get("last_check"),
                ),
            )
    conn.commit()
    try:
        legacy.rename(legacy.with_suffix(".json.migrated"))
    except OSError:
        pass


def init_db() -> None:
    global _db_ready
    if _db_ready:
        return
    with _connect() as conn:
        _init_schema(conn)
        conn.commit()
        _migrate_json_if_needed(conn)
        conn.commit()
    _db_ready = True


def _ensure_user(conn: sqlite3.Connection, chat_id: str, default_lang: str = "ua") -> None:
    conn.execute(
        "INSERT OR IGNORE INTO users (chat_id, lang) VALUES (?, ?)",
        (chat_id, default_lang),
    )


def _row_to_cert(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "label": row["label"],
        "pnr": row["pnr"],
        "center_date": row["center_date"],
        "birth": row["birth"],
        "added_at": row["added_at"],
        "last_status": row["last_status"],
        "last_check": row["last_check"],
    }


# ── Public API (синхронно, як раніше — виклики з async-хендлерів PTB) ─────────


def get_lang(chat_id) -> str:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        row = conn.execute("SELECT lang FROM users WHERE chat_id = ?", (cid,)).fetchone()
        return row["lang"] if row else "ua"


def set_lang(chat_id, lang: str) -> None:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users (chat_id, lang) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET lang = excluded.lang",
            (cid, lang),
        )
        conn.commit()


def get_certs(chat_id) -> list[dict]:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, label, pnr, center_date, birth, added_at, last_status, last_check "
            "FROM certs WHERE chat_id = ? ORDER BY id",
            (cid,),
        ).fetchall()
        return [_row_to_cert(r) for r in rows]


def get_cert(chat_id, cert_id: int) -> dict | None:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, label, pnr, center_date, birth, added_at, last_status, last_check "
            "FROM certs WHERE chat_id = ? AND id = ?",
            (cid, cert_id),
        ).fetchone()
        return _row_to_cert(row) if row else None


def count_certs(chat_id) -> int:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        r = conn.execute(
            "SELECT COUNT(*) AS c FROM certs WHERE chat_id = ?", (cid,)
        ).fetchone()
        return int(r["c"])


def can_add_cert(chat_id) -> bool:
    return count_certs(chat_id) < MAX_CERTS


def add_cert(chat_id, label: str, pnr: str, center_date: str, birth: str) -> dict:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        _ensure_user(conn, cid)
        row = conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 AS n FROM certs WHERE chat_id = ?", (cid,)
        ).fetchone()
        next_id = int(row["n"])
        cert = {
            "id": next_id,
            "label": label,
            "pnr": pnr,
            "center_date": center_date,
            "birth": birth,
            "added_at": datetime.now().isoformat(),
            "last_status": "not_found",
            "last_check": None,
        }
        conn.execute(
            """
            INSERT INTO certs (
                chat_id, id, label, pnr, center_date, birth,
                added_at, last_status, last_check
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                cert["id"],
                cert["label"],
                cert["pnr"],
                cert["center_date"],
                cert["birth"],
                cert["added_at"],
                cert["last_status"],
                cert["last_check"],
            ),
        )
        conn.commit()
        return cert


def delete_cert(chat_id, cert_id: int) -> bool:
    init_db()
    cid = str(chat_id)
    with _connect() as conn:
        cur = conn.execute("DELETE FROM certs WHERE chat_id = ? AND id = ?", (cid, cert_id))
        conn.commit()
        return cur.rowcount > 0


def update_cert_status(chat_id, cert_id: int, status: str) -> None:
    init_db()
    cid = str(chat_id)
    now = datetime.now().isoformat()
    with _connect() as conn:
        conn.execute(
            """
            UPDATE certs SET last_status = ?, last_check = ?
            WHERE chat_id = ? AND id = ?
            """,
            (status, now, cid, cert_id),
        )
        conn.commit()


def get_all_users() -> dict:
    """Формат як у старому JSON — для scheduler."""
    init_db()
    with _connect() as conn:
        users: dict[str, dict] = {}
        for row in conn.execute("SELECT chat_id, lang FROM users"):
            users[row["chat_id"]] = {"lang": row["lang"], "certs": []}
        for row in conn.execute(
            "SELECT chat_id, id, label, pnr, center_date, birth, added_at, last_status, last_check "
            "FROM certs ORDER BY chat_id, id"
        ):
            cid = row["chat_id"]
            if cid not in users:
                users[cid] = {"lang": "ua", "certs": []}
            users[cid]["certs"].append(_row_to_cert(row))
        return users
