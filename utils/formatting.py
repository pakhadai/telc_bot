"""
utils/formatting.py — helpers that turn CertResult into Telegram messages.
"""

from config import CertResult
from i18n import t
from utils.dates import now_str


def _build_scores_block(result: CertResult, _lang: str) -> str:
    """
    Будує текстовий блок з усіма балами:
      Schriftliche Prüfung: 169.5 / 225
        ├ Leseverstehen: 60 / 75
        ...
      Mündliche Prüfung: 67 / 75
        ...
      Summe: 236.5 / 300
    """
    lines: list[str] = []

    if result.score_written:
        lines.append(f"*Schriftliche Prüfung:* {result.score_written}")
        for i, (title, score) in enumerate(result.score_written_details):
            connector = "└" if i == len(result.score_written_details) - 1 else "├"
            lines.append(f"  {connector} {title}: {score}")

    if result.score_oral:
        lines.append(f"*Mündliche Prüfung:* {result.score_oral}")
        for i, (title, score) in enumerate(result.score_oral_details):
            connector = "└" if i == len(result.score_oral_details) - 1 else "├"
            lines.append(f"  {connector} {title}: {score}")

    if result.score_total:
        lines.append(f"*Summe:* {result.score_total}")

    return "\n".join(lines) if lines else "—"


def format_result(pnr: str, result: CertResult, lang: str) -> str:
    """Return a fully formatted Telegram message for a given CertResult."""
    if not result.found:
        return t("result_not_found", lang,
                 pnr=pnr,
                 n=result.dates_checked,
                 time=now_str())

    status_text = (
        t(result.status, lang)
        if result.status in ("passed", "failed")
        else t("not_found", lang)
    )

    has_scores = bool(result.score_total or result.score_written or result.score_oral)

    if has_scores:
        scores_block = _build_scores_block(result, lang)
        ct = result.cert_type or "digital"
        return t("result_full", lang,
                 pnr=pnr,
                 cert_type_label=t(f"cert_type_{ct}", lang),
                 exam_name=result.exam_name or "—",
                 issue_date=result.issue_date,
                 exam_date=result.exam_date or "—",
                 exam_center=result.exam_center or "—",
                 scores_block=scores_block,
                 praedikat=result.praedikat or "—",
                 status=status_text)

    return t("result_digital", lang,
             pnr=pnr,
             exam_name=result.exam_name or "—",
             issue_date=result.issue_date,
             status=status_text)
