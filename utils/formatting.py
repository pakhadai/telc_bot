"""
utils/formatting.py — helpers that turn CertResult into Telegram messages.
"""

from config import CertResult
from i18n import t
from utils.dates import now_str


def format_result(pnr: str, result: CertResult, lang: str) -> str:
    """Return a fully formatted Telegram message for a given CertResult."""
    if not result.found:
        return t("result_not_found", lang,
                 pnr=pnr,
                 n=result.dates_checked,
                 time=now_str())

    status_text = t(result.status, lang) if result.status in ("passed", "failed") else t("not_found", lang)

    if result.cert_type == "digital":
        return t("result_digital", lang,
                 pnr=pnr,
                 exam_name=result.exam_name or "—",
                 issue_date=result.issue_date,
                 status=status_text)

    # paper certificate — full details
    return t("result_paper", lang,
             pnr=pnr,
             exam_name=result.exam_name or "—",
             issue_date=result.issue_date,
             exam_date=result.exam_date or "—",
             exam_center=result.exam_center or "—",
             score_total=result.score_total or "—",
             score_written=result.score_written or "—",
             score_oral=result.score_oral or "—",
             praedikat=result.praedikat or "—",
             status=status_text)
