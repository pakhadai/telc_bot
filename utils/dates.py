"""
utils/dates.py — date helpers for the TELC bot.
"""

from datetime import datetime, timedelta


def date_range(center: str, days: int) -> list[str]:
    """Return list of DD.MM.YYYY dates from center-days to center+days."""
    dt = datetime.strptime(center, "%d.%m.%Y")
    return [
        (dt + timedelta(days=d)).strftime("%d.%m.%Y")
        for d in range(-days, days + 1)
    ]


def date_range_bounds(center: str, days: int) -> tuple[str, str]:
    dt = datetime.strptime(center, "%d.%m.%Y")
    start = (dt - timedelta(days=days)).strftime("%d.%m.%Y")
    end = (dt + timedelta(days=days)).strftime("%d.%m.%Y")
    return start, end


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
