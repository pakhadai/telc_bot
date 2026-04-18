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


def format_test_result(pnr: str, lang: str, found: bool) -> str:
    """Return a test-mode message (no real TELC query)."""
    import random
    header = t("test_header", lang)
    if found:
        fake = CertResult(
            found=True,
            cert_type="paper",
            issue_date="13.11.2025",
            status="passed",
            praedikat="Sehr gut",
            score_total="271,0 / 300",
            score_written="197,0 / 225",
            score_oral="74,0 / 75",
            exam_name="telc Deutsch B1",
            exam_date="27.10.2025",
            exam_center="HDS St. Gallen AG",
        )
        return header + format_result(pnr, fake, lang)
    else:
        fake = CertResult(found=False, dates_checked=43)
        return header + format_result(pnr, fake, lang)
