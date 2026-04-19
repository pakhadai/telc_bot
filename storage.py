"""
storage.py — PostgreSQL (Railway DATABASE_URL) або SQLite (локально / SQLITE_PATH).

Міграція з users_data.json — якщо таблиці порожні й файл є, один раз імпорт.

Railway: Database → PostgreSQL (не Redis). У сервісі бота додай змінну DATABASE_URL
(Reference на Postgres), або змонтуй volume + SQLite без окремої БД.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from config import DATA_FILE, DATABASE_URL, SQLITE_PATH

logger = logging.getLogger(__name__)

MAX_CERTS = 5

_db_ready = False
_USE_PG = bool(DATABASE_URL)

_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    chat_id TEXT PRIMARY KEY,
    lang TEXT NOT NULL DEFAULT 'ua'
);
"""
_CREATE_CERTS = """
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
"""
_CREATE_INDEX = "CREATE INDEX IF NOT EXISTS idx_certs_chat ON certs(chat_id);"


def _row_get(row: Any, key: str, default=None):
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


def _adapt_sql(sql: str) -> str:
    if _USE_PG:
        return sql.replace("?", "%s")
    return sql


def _connect_sqlite() -> sqlite3.Connection:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SQLITE_PATH), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def _session() -> Iterator[Any]:
    """Уніфікована сесія: Postgres (psycopg) або SQLite."""
    if _USE_PG:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=20)
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = _connect_sqlite()
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()


def _execute(conn, sql: str, params: tuple = (), fetch: str | None = None):
    sql = _adapt_sql(sql)
    cur = conn.execute(sql, params)
    if fetch == "one":
        return cur.fetchone()
    if fetch == "all":
        return cur.fetchall()
    return cur


def _init_schema(conn: Any) -> None:
    _execute(conn, _CREATE_USERS)
    _execute(conn, _CREATE_CERTS)
    _execute(conn, _CREATE_INDEX)


def _ensure_cert_extra_columns(conn: Any) -> None:
    """ALTER TABLE: completed_at, cached_result, initial_sweep_done."""
    if _USE_PG:
        _execute(
            conn,
            "ALTER TABLE certs ADD COLUMN IF NOT EXISTS completed_at TEXT",
        )
        _execute(
            conn,
            "ALTER TABLE certs ADD COLUMN IF NOT EXISTS cached_result TEXT",
        )
        _execute(
            conn,
            "ALTER TABLE certs ADD COLUMN IF NOT EXISTS initial_sweep_done BOOLEAN NOT NULL DEFAULT FALSE",
        )
    else:
        rows = _execute(conn, "PRAGMA table_info(certs)", fetch="all") or []
        names = {r["name"] for r in rows}
        if "completed_at" not in names:
            _execute(conn, "ALTER TABLE certs ADD COLUMN completed_at TEXT")
        if "cached_result" not in names:
            _execute(conn, "ALTER TABLE certs ADD COLUMN cached_result TEXT")
        if "initial_sweep_done" not in names:
            _execute(
                conn,
                "ALTER TABLE certs ADD COLUMN initial_sweep_done INTEGER NOT NULL DEFAULT 0",
            )


def _migrate_json_if_needed(conn: Any) -> None:
    row = _execute(conn, "SELECT COUNT(*) AS c FROM users", fetch="one")
    n = int(row["c"]) if row is not None else 0
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
    back = "PostgreSQL" if _USE_PG else "SQLite"
    logger.info("Migrating %d user(s) from %s to %s", len(data), legacy, back)
    for cid, u in data.items():
        if not isinstance(u, dict):
            continue
        lang = str(u.get("lang", "ua"))
        _execute(
            conn,
            "INSERT INTO users (chat_id, lang) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET lang = excluded.lang",
            (str(cid), lang),
        )
        for c in u.get("certs") or []:
            if not isinstance(c, dict):
                continue
            _execute(
                conn,
                """
                INSERT INTO certs (
                    chat_id, id, label, pnr, center_date, birth,
                    added_at, last_status, last_check,
                    completed_at, cached_result, initial_sweep_done
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, id) DO UPDATE SET
                    label = excluded.label,
                    pnr = excluded.pnr,
                    center_date = excluded.center_date,
                    birth = excluded.birth,
                    added_at = excluded.added_at,
                    last_status = excluded.last_status,
                    last_check = excluded.last_check,
                    completed_at = excluded.completed_at,
                    cached_result = excluded.cached_result,
                    initial_sweep_done = excluded.initial_sweep_done
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
                    c.get("completed_at"),
                    c.get("cached_result"),
                    bool(c.get("initial_sweep_done")),
                ),
            )
    try:
        legacy.rename(legacy.with_suffix(".json.migrated"))
    except OSError:
        pass


def init_db() -> None:
    global _db_ready
    if _db_ready:
        return
    with _session() as conn:
        _init_schema(conn)
        _ensure_cert_extra_columns(conn)
        _migrate_json_if_needed(conn)
    _db_ready = True


def backend_label() -> str:
    return "postgresql" if _USE_PG else "sqlite"


def _parse_cached_result(raw: Any) -> dict | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            out = json.loads(raw)
            return out if isinstance(out, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _row_to_cert(row: Any) -> dict[str, Any]:
    if row is None:
        raise TypeError("row is None")
    raw_cached = _row_get(row, "cached_result")
    return {
        "id": row["id"],
        "label": row["label"],
        "pnr": row["pnr"],
        "center_date": row["center_date"],
        "birth": row["birth"],
        "added_at": row["added_at"],
        "last_status": row["last_status"],
        "last_check": row["last_check"],
        "completed_at": _row_get(row, "completed_at"),
        "cached_result": _parse_cached_result(raw_cached),
        "initial_sweep_done": bool(_row_get(row, "initial_sweep_done")),
    }


# ── Public API ────────────────────────────────────────────────────────────────


def get_lang(chat_id) -> str:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        row = _execute(
            conn, "SELECT lang FROM users WHERE chat_id = ?", (cid,), fetch="one"
        )
        return row["lang"] if row else "ua"


def set_lang(chat_id, lang: str) -> None:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        _execute(
            conn,
            "INSERT INTO users (chat_id, lang) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET lang = excluded.lang",
            (cid, lang),
        )


def get_certs(chat_id) -> list[dict]:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        rows = _execute(
            conn,
            "SELECT id, label, pnr, center_date, birth, added_at, last_status, last_check, "
            "completed_at, cached_result, initial_sweep_done "
            "FROM certs WHERE chat_id = ? ORDER BY id",
            (cid,),
            fetch="all",
        )
        return [_row_to_cert(r) for r in (rows or [])]


def get_cert(chat_id, cert_id: int) -> dict | None:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        row = _execute(
            conn,
            "SELECT id, label, pnr, center_date, birth, added_at, last_status, last_check, "
            "completed_at, cached_result, initial_sweep_done "
            "FROM certs WHERE chat_id = ? AND id = ?",
            (cid, cert_id),
            fetch="one",
        )
        return _row_to_cert(row) if row else None


def count_certs(chat_id) -> int:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        r = _execute(
            conn, "SELECT COUNT(*) AS c FROM certs WHERE chat_id = ?", (cid,), fetch="one"
        )
        return int(r["c"])


def can_add_cert(chat_id) -> bool:
    return count_certs(chat_id) < MAX_CERTS


def add_cert(chat_id, label: str, pnr: str, center_date: str, birth: str) -> dict:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        _execute(
            conn,
            "INSERT INTO users (chat_id, lang) VALUES (?, ?) "
            "ON CONFLICT(chat_id) DO NOTHING",
            (cid, "ua"),
        )
        row = _execute(
            conn,
            "SELECT COALESCE(MAX(id), 0) + 1 AS n FROM certs WHERE chat_id = ?",
            (cid,),
            fetch="one",
        )
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
            "initial_sweep_done": False,
        }
        _execute(
            conn,
            """
            INSERT INTO certs (
                chat_id, id, label, pnr, center_date, birth,
                added_at, last_status, last_check, completed_at, cached_result,
                initial_sweep_done
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                None,
                None,
                False,
            ),
        )
        return cert


def delete_cert(chat_id, cert_id: int) -> bool:
    init_db()
    cid = str(chat_id)
    with _session() as conn:
        cur = _execute(conn, "DELETE FROM certs WHERE chat_id = ? AND id = ?", (cid, cert_id))
        rc = cur.rowcount if hasattr(cur, "rowcount") else 0
        return int(rc or 0) > 0


def set_initial_sweep_done(chat_id, cert_id: int, done: bool = True) -> None:
    """Після першого повного проходу «іспит → сьогодні» без знахідки — увімкнути фазу 2 (rolling)."""
    init_db()
    cid = str(chat_id)
    val = bool(done)
    with _session() as conn:
        _execute(
            conn,
            """
            UPDATE certs SET initial_sweep_done = ?
            WHERE chat_id = ? AND id = ?
            """,
            (val, cid, cert_id),
        )


def update_cert_status(chat_id, cert_id: int, status: str) -> None:
    init_db()
    cid = str(chat_id)
    now = datetime.now().isoformat()
    with _session() as conn:
        _execute(
            conn,
            """
            UPDATE certs SET last_status = ?, last_check = ?
            WHERE chat_id = ? AND id = ?
            """,
            (status, now, cid, cert_id),
        )


_EDITABLE_FIELDS = frozenset({"label", "pnr", "center_date", "birth"})


def save_cert_completion(
    chat_id, cert_id: int, status: str, formatted_block: str
) -> None:
    """Зберегти текст результату (format_result) і позначити перевірку завершеною."""
    init_db()
    cid = str(chat_id)
    now = datetime.now().isoformat()
    blob = json.dumps({"formatted": formatted_block}, ensure_ascii=False)
    with _session() as conn:
        _execute(
            conn,
            """
            UPDATE certs SET
                last_status = ?,
                last_check = ?,
                completed_at = ?,
                cached_result = ?
            WHERE chat_id = ? AND id = ?
            """,
            (status, now, now, blob, cid, cert_id),
        )


def update_cert_field(chat_id, cert_id: int, field: str, value: str) -> bool:
    if field not in _EDITABLE_FIELDS:
        raise ValueError(f"Unsupported field: {field}")
    init_db()
    cid = str(chat_id)
    val = value.strip()
    if field == "label" and not val:
        return False
    if field in ("pnr", "center_date", "birth") and not val:
        return False
    with _session() as conn:
        row = _execute(
            conn,
            "SELECT 1 FROM certs WHERE chat_id = ? AND id = ?",
            (cid, cert_id),
            fetch="one",
        )
        if not row:
            return False
        if field in ("pnr", "center_date"):
            _execute(
                conn,
                f"""
                UPDATE certs SET {field} = ?,
                    completed_at = NULL,
                    cached_result = NULL,
                    initial_sweep_done = ?
                WHERE chat_id = ? AND id = ?
                """,
                (val, False, cid, cert_id),
            )
        else:
            _execute(
                conn,
                f"""
                UPDATE certs SET {field} = ?
                WHERE chat_id = ? AND id = ?
                """,
                (val, cid, cert_id),
            )
    return True


def get_all_users() -> dict:
    """Формат як у старому JSON — для scheduler."""
    init_db()
    with _session() as conn:
        users: dict[str, dict] = {}
        for row in _execute(conn, "SELECT chat_id, lang FROM users", fetch="all") or []:
            users[str(row["chat_id"])] = {"lang": row["lang"], "certs": []}
        all_certs = _execute(
            conn,
            "SELECT chat_id, id, label, pnr, center_date, birth, added_at, last_status, last_check, "
            "completed_at, cached_result, initial_sweep_done "
            "FROM certs ORDER BY chat_id, id",
            fetch="all",
        ) or []
        for row in all_certs:
            cid = row["chat_id"]
            if cid not in users:
                users[cid] = {"lang": "ua", "certs": []}
            users[cid]["certs"].append(_row_to_cert(row))
        return users
