"""
utils/dates.py — date helpers for the TELC bot.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from config import PHASE1_MAX_SPAN_DAYS, ROLLING_SCAN_DAYS, SCHEDULER_TIMEZONE


def _midnight_in_scheduler_tz() -> datetime:
    tz = ZoneInfo(SCHEDULER_TIMEZONE)
    return datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)


def telc_pruefung_dates(exam_date: str, initial_sweep_done: bool) -> list[str]:
    """
    Дати DD.MM.YYYY для lookup на results.telc.net.

    Фаза 1 (initial_sweep_done=False): від дати іспиту до «сьогодні» (Berlin), хронологічно.
    Фаза 2: лише останні ROLLING_SCAN_DAYS+1 днів до сьогодні; порядок — від сьогодні назад.
    """
    tz = ZoneInfo(SCHEDULER_TIMEZONE)
    exam = datetime.strptime(exam_date.strip(), "%d.%m.%Y").replace(tzinfo=tz)
    today = _midnight_in_scheduler_tz()

    if not initial_sweep_done:
        if exam > today:
            return []
        lo = exam
        span_days = (today - exam).days
        if span_days > PHASE1_MAX_SPAN_DAYS:
            lo = today - timedelta(days=PHASE1_MAX_SPAN_DAYS)
        out: list[str] = []
        cur = lo
        while cur <= today:
            out.append(cur.strftime("%d.%m.%Y"))
            cur += timedelta(days=1)
        return out

    lo = today - timedelta(days=ROLLING_SCAN_DAYS)
    out = []
    cur = today
    while cur >= lo:
        out.append(cur.strftime("%d.%m.%Y"))
        cur -= timedelta(days=1)
    return out


def describe_cert_scan_range(
    exam_date: str,
    lang: str,
    *,
    initial_sweep_done: bool,
    completed_at: str | None,
) -> str:
    """Текст у повідомленнях про те, які дати Prüfung зараз перебирає бот."""
    from i18n import t

    if completed_at:
        return t("search_range_saved", lang)
    if not initial_sweep_done:
        cands = telc_pruefung_dates(exam_date, False)
        if not cands:
            today = _midnight_in_scheduler_tz().strftime("%d.%m.%Y")
            return t("scan_exam_future", lang, exam=exam_date, today=today)
        return t("scan_phase1_desc", lang, start=cands[0], end=cands[-1])
    cands = telc_pruefung_dates(exam_date, True)
    if not cands:
        return t("scan_phase2_empty", lang)
    return t("scan_phase2_desc", lang, lo=cands[-1], hi=cands[0])


def next_check_time() -> str:
    """Return HH:MM CET of the next scheduled check."""
    now = datetime.now()
    for h, m in [(9, 0), (17, 0)]:
        candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if candidate > now:
            return candidate.strftime("%H:%M CET")
    tomorrow = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0)
    return tomorrow.strftime("%d.%m %H:%M CET")


def is_valid_date(text: str) -> bool:
    try:
        datetime.strptime(text.strip(), "%d.%m.%Y")
        return True
    except ValueError:
        return False


def now_str() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def format_last_check(raw: str | None) -> str:
    """Локальна дата/час з ISO з БД, або «—» якщо ще не перевіряли."""
    if not raw or not str(raw).strip():
        return "—"
    s = str(raw).strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return s
