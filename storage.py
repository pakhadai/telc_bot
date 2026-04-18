"""
storage.py — JSON persistence, multi-certificate support.

Schema per chat_id:
{
  "lang": "ua",
  "certs": [
    {
      "id": 1,
      "label": "Dmytro B1",
      "pnr": "4627704",
      "center_date": "13.11.2025",
      "birth": "23.02.1994",
      "added_at": "2025-11-01T10:00:00",
      "last_status": "not_found",
      "last_check": null
    }
  ]
}
Max MAX_CERTS certificates per user.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from config import DATA_FILE

logger = logging.getLogger(__name__)
_path = Path(DATA_FILE)
MAX_CERTS = 5


def _load() -> dict:
    if _path.exists():
        try:
            with open(_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load data file: %s", exc)
    return {}


def _save(data: dict) -> None:
    try:
        with open(_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        logger.error("Failed to save data file: %s", exc)


def _user(data: dict, cid: str) -> dict:
    if cid not in data:
        data[cid] = {"lang": "ua", "certs": []}
    if "certs" not in data[cid]:
        data[cid]["certs"] = []
    return data[cid]


def _next_id(certs: list) -> int:
    return max((c["id"] for c in certs), default=0) + 1


# ── Public API ────────────────────────────────────────────────────────────────

def get_lang(chat_id) -> str:
    return _load().get(str(chat_id), {}).get("lang", "ua")


def set_lang(chat_id, lang: str) -> None:
    data = _load()
    _user(data, str(chat_id))["lang"] = lang
    _save(data)


def get_certs(chat_id) -> list[dict]:
    data = _load()
    return _user(data, str(chat_id))["certs"]


def get_cert(chat_id, cert_id: int) -> dict | None:
    return next((c for c in get_certs(chat_id) if c["id"] == cert_id), None)


def count_certs(chat_id) -> int:
    return len(get_certs(chat_id))


def can_add_cert(chat_id) -> bool:
    return count_certs(chat_id) < MAX_CERTS


def add_cert(chat_id, label: str, pnr: str, center_date: str, birth: str) -> dict:
    data = _load()
    cid = str(chat_id)
    user = _user(data, cid)
    cert = {
        "id":          _next_id(user["certs"]),
        "label":       label,
        "pnr":         pnr,
        "center_date": center_date,
        "birth":       birth,
        "added_at":    datetime.now().isoformat(),
        "last_status": "not_found",
        "last_check":  None,
    }
    user["certs"].append(cert)
    _save(data)
    return cert


def delete_cert(chat_id, cert_id: int) -> bool:
    data = _load()
    cid = str(chat_id)
    user = _user(data, cid)
    before = len(user["certs"])
    user["certs"] = [c for c in user["certs"] if c["id"] != cert_id]
    if len(user["certs"]) < before:
        _save(data)
        return True
    return False


def update_cert_status(chat_id, cert_id: int, status: str) -> None:
    data = _load()
    cid = str(chat_id)
    for cert in _user(data, cid)["certs"]:
        if cert["id"] == cert_id:
            cert["last_status"] = status
            cert["last_check"]  = datetime.now().isoformat()
            break
    _save(data)


def get_all_users() -> dict:
    return _load()
