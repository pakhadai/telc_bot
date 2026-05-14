"""
config.py — всі константи та CertResult dataclass.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent


def _database_url() -> str | None:
    """
    Postgres: DATABASE_URL з Docker Compose, Railway тощо (інколи префікс postgres://).
    Якщо задано — storage використовує PostgreSQL замість SQLite.
    """
    raw = (os.getenv("DATABASE_URL") or "").strip()
    if not raw:
        return None
    if raw.startswith("postgres://"):
        return "postgresql://" + raw[len("postgres://") :]
    return raw


def _read_bot_token() -> str:
    """VPS / Docker / Railway: змінна `BOT_TOKEN`. Дублікат імені: `TELEGRAM_BOT_TOKEN`."""
    raw = (os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    return raw if raw else "YOUR_BOT_TOKEN_HERE"


# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = _read_bot_token()

# ── TELC portal ───────────────────────────────────────────────────────────────
TELC_URL: str = "https://results.telc.net/"

# Після першого повного проходу «дата іспиту → сьогодні» без результату:
# лише останні N календарних днів (включно з сьогодні) як дати Prüfung.
ROLLING_SCAN_DAYS: int = int(os.getenv("ROLLING_SCAN_DAYS", "7"))
# Максимум календарних днів за один прохід фази 1 (захист від дуже старої дати іспиту).
PHASE1_MAX_SPAN_DAYS: int = int(os.getenv("PHASE1_MAX_SPAN_DAYS", "400"))

# ── Scheduler ─────────────────────────────────────────────────────────────────
# Автоматична перевірка — один раз на день (Europe/Berlin).
# Окремо лишається 1 ручна перевірка на день з меню.
CHECK_TIMES: list[tuple[int, int]] = [(15, 0)]
SCHEDULER_TIMEZONE: str = "Europe/Berlin"

# Затримка між перевірками різних користувачів (щоб не перевантажувати API)
USER_DELAY_SECONDS: float = 2.0

# ── Persistence ───────────────────────────────────────────────────────────────
# PostgreSQL: змінна DATABASE_URL (Compose, Railway тощо).
# SQLite: якщо DATABASE_URL немає — файл SQLITE_PATH (том на VPS / Railway за бажання).
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
    score_written_details: list[tuple[str, str]] = field(default_factory=list)
    score_oral_details: list[tuple[str, str]] = field(default_factory=list)
