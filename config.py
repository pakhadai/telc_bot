"""
config.py — всі константи та CertResult dataclass.
"""
import os
from dataclasses import dataclass
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent


def _database_url() -> str | None:
    """
    Railway Postgres дає DATABASE_URL (інколи з префіксом postgres://).
    Якщо задано — storage використовує PostgreSQL замість SQLite.
    """
    raw = (os.getenv("DATABASE_URL") or "").strip()
    if not raw:
        return None
    if raw.startswith("postgres://"):
        return "postgresql://" + raw[len("postgres://") :]
    return raw


def _read_bot_token() -> str:
    """Railway / Docker: змінна `BOT_TOKEN`. Дублікат імені: `TELEGRAM_BOT_TOKEN`."""
    raw = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    return raw if raw else "YOUR_BOT_TOKEN_HERE"


# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = _read_bot_token()

# ── TELC portal ───────────────────────────────────────────────────────────────
TELC_URL: str = "https://results.telc.net/"

# Скільки днів ± від введеної дати перебирати
DATE_SEARCH_RANGE: int = 21

# ── Scheduler ─────────────────────────────────────────────────────────────────
CHECK_TIMES: list[tuple[int, int]] = [(9, 0), (17, 0)]   # Europe/Berlin
SCHEDULER_TIMEZONE: str = "Europe/Berlin"

# Затримка між перевірками різних користувачів (щоб не перевантажувати API)
USER_DELAY_SECONDS: float = 2.0

# ── Persistence ───────────────────────────────────────────────────────────────
# PostgreSQL: змінна DATABASE_URL (Railway підставляє з плагіна Postgres).
# SQLite: якщо DATABASE_URL немає — файл SQLITE_PATH (volume на Railway за бажання).
DATABASE_URL: str | None = _database_url()
SQLITE_PATH: Path = Path(
    os.getenv("SQLITE_PATH", str(_BASE_DIR / "telc_bot.sqlite"))
).expanduser()
# Легасі JSON — лише одноразова міграція в SQLite, якщо БД порожня
DATA_FILE: Path = _BASE_DIR / os.getenv("USERS_JSON_LEGACY", "users_data.json")
LOG_FILE: str = "telc_bot.log"


# ── CertResult ────────────────────────────────────────────────────────────────
@dataclass
class CertResult:
    """Результат одного scrape-запиту."""
    found: bool         = False
    cert_type: str      = ""       # "digital" | "paper" | ""
    issue_date: str     = ""
    status: str         = ""       # "passed" | "failed" | "not_found" | "error"
    praedikat: str      = ""       # "Sehr gut", "Gut", ...
    score_total: str    = ""       # "271 / 300"
    score_written: str  = ""       # "197 / 225"
    score_oral: str     = ""       # "74 / 75"
    exam_name: str      = ""       # "telc Deutsch B1"
    exam_date: str      = ""       # "27.10.2025"
    exam_center: str    = ""       # "HDS St. Gallen AG"
    dates_checked: int  = 0
    error_message: str  = ""
