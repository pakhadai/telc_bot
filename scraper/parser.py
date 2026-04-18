"""
scraper/parser.py — парсинг реальних API відповідей results.telc.net

=== Верифікована структура (з test_api.py) ===

Lookup response:
  {examinationInstituteId, examId, attendeeId, isVirtualBadge, virtualBadgeCredential}

Certificate detail response:
  {
    "language": "de",
    "content": [
      {
        "type": "certHead",
        "content": [
          {"type": "headline1", "content": "Zertifikat"},
          {"type": "headline2", "content": "telc Deutsch B1"},
          {"type": "subheadline", "content": "Europaratsstufe B1 ..."}
        ]
      },
      {
        "type": "personalData",
        "content": [
          {"type": "lastname",    "content": "Pakhadai"},
          {"type": "firstname",  "content": "Dmytro"},
          {"type": "dateOfBirth","content": "1994-02-23"},
          {"type": "placeOfBirth","content": "Odesa / UA"}
        ]
      },
      {
        "type": "grades",
        "content": [
          {                                   ← Schriftliche Prüfung (isMainTotal: true)
            "type": "pointsAndTotal",
            "title": "Schriftliche Prüfung",
            "content": "197",               ← string!
            "maxPoints": 225,               ← int!
            "decimalPlaces": 1,
            "specialConditions": "false",
            "isMainTotal": true
          },
          {"type":"pointsAndTotal","title":"Leseverstehen",         "content":"70",   "maxPoints":75,  "decimalPlaces":1},
          {"type":"pointsAndTotal","title":"Sprachbausteine",       "content":"19.5", "maxPoints":30,  "decimalPlaces":1},
          {"type":"pointsAndTotal","title":"Hörverstehen",          "content":"62.5", "maxPoints":75,  "decimalPlaces":1},
          {"type":"pointsAndTotal","title":"Schriftlicher Ausdruck","content":"45",   "maxPoints":45,  "decimalPlaces":1},
          {                                   ← Mündliche Prüfung (isMainTotal: true)
            "type": "pointsAndTotal",
            "title": "Mündliche Prüfung",
            "content": "74", "maxPoints": 75, "isMainTotal": true
          },
          {"type":"pointsAndTotal","title":"Kontaktaufnahme",           "content":"14", "maxPoints":15},
          {"type":"pointsAndTotal","title":"Gespräch über ein Thema",   "content":"30", "maxPoints":30},
          {"type":"pointsAndTotal","title":"Gemeinsam eine Aufgabe",    "content":"30", "maxPoints":30},
          {                                   ← Summe (isMainTotal: true)
            "type": "pointsAndTotal",
            "title": "Summe",
            "content": "271", "maxPoints": 300, "isMainTotal": true
          },
          {                                   ← Prädikat
            "type": "sumPredicate",
            "title": "Prädikat",
            "content": "1",                 ← grade key
            "showLabel": true
          }
        ]
      },
      {
        "type": "generalData",               ← ОСТАННІЙ блок (не третій!)
        "content": [
          {"type": "date",        "title": "Datum der Prüfung",     "content": "2025-10-27"},
          {"type": "titleAndText","title": "Teilnehmernummer",      "content": "4627704"},
          {"type": "date",        "title": "Datum der Ausstellung", "content": "2025-11-13"},
          {"type": "titleAndText","title": "Prüfungszentrum",       "content": "HDS St. Gallen AG"}
        ]
      }
    ]
  }
"""

import logging
from config import CertResult

logger = logging.getLogger(__name__)

# Grades mapping (from JS source: certificateFields.grades)
GRADE_MAP = {
    "1": "Sehr gut",
    "2": "Gut",
    "3": "Befriedigend",
    "4": "Ausreichend",
    "B": "Bestanden",
    "F": "Nicht bestanden",
}


def _block(blocks: list[dict], block_type: str) -> dict:
    """Знайти перший блок за типом."""
    return next((b for b in blocks if b.get("type") == block_type), {})


def _content_by_title(blocks: list[dict], keyword: str) -> str:
    """Знайти content за ключовим словом в title (case-insensitive)."""
    kw = keyword.lower()
    for b in blocks:
        if kw in str(b.get("title", "")).lower():
            return str(b.get("content", "")).strip()
    return ""


def _score_str(block: dict) -> str:
    """
    Форматує 'content / maxPoints' з урахуванням що:
    - content: string ("197", "19.5")
    - maxPoints: int (225) або string
    """
    pts = str(block.get("content", "")).strip()
    mx  = str(block.get("maxPoints", "")).strip()
    dec = int(block.get("decimalPlaces", 1))

    # Форматуємо бали з правильною кількістю знаків після коми
    try:
        pts_f = float(pts)
        pts_fmt = f"{pts_f:.{dec}f}".rstrip("0").rstrip(".")
        # Якщо .0 — показуємо без дробу для читабельності
        if "." not in pts_fmt:
            pts_fmt = pts_fmt
    except ValueError:
        pts_fmt = pts

    return f"{pts_fmt} / {mx}" if mx else pts_fmt


def _reformat_date(iso_str: str) -> str:
    """YYYY-MM-DD → DD.MM.YYYY. Повертає як є якщо інший формат."""
    if not iso_str:
        return ""
    s = str(iso_str).strip().split("T")[0].split(" ")[0]
    parts = s.split("-")
    if len(parts) == 3 and len(parts[0]) == 4:
        return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return s


def parse_certificate_response(
    lookup_data: dict,
    detail_data: dict | None,
    cert_type: str,
    issue_date: str,
) -> CertResult:
    """
    Будує CertResult з lookup + detail відповідей API.
    Graceful fallback якщо detail_data відсутній.
    """
    if not detail_data:
        logger.warning("No detail data — using lookup only (attendeeId=%s)",
                       lookup_data.get("attendeeId", "?")[:8])
        return CertResult(
            found=True,
            cert_type=cert_type,
            issue_date=issue_date,
            status="passed",
            error_message=(
                f"attendeeId={lookup_data.get('attendeeId', '')} "
                f"examId={lookup_data.get('examId', '')}"
            ),
        )

    top = detail_data.get("content", [])

    # ── certHead → назва іспиту ───────────────────────────────────────────────
    head_content = _block(top, "certHead").get("content", [])
    exam_name = _block(head_content, "headline2").get("content", "") or ""

    # ── grades → оцінки та Prädikat ───────────────────────────────────────────
    grades_content = _block(top, "grades").get("content", [])

    score_written = ""
    score_oral    = ""
    score_total   = ""

    for b in grades_content:
        if not b.get("isMainTotal"):
            continue
        title = str(b.get("title", "")).lower()
        if "schriftlich" in title:
            score_written = _score_str(b)
        elif "mündlich" in title or "mundlich" in title or "oral" in title:
            score_oral = _score_str(b)
        elif "summe" in title or "gesamt" in title or "total" in title:
            score_total = _score_str(b)

    # Prädikat
    pred_block    = _block(grades_content, "sumPredicate")
    praedikat_key = str(pred_block.get("content", "")).strip()
    praedikat     = GRADE_MAP.get(praedikat_key, praedikat_key)
    status        = "failed" if praedikat_key == "F" else "passed"

    # ── generalData → дати та центр ───────────────────────────────────────────
    general_content = _block(top, "generalData").get("content", [])

    exam_date_raw  = _content_by_title(general_content, "Datum der Prüfung")
    issue_date_raw = _content_by_title(general_content, "Datum der Ausstellung")
    exam_center    = _content_by_title(general_content, "Prüfungszentrum")

    exam_date  = _reformat_date(exam_date_raw)
    if issue_date_raw:
        issue_date = _reformat_date(issue_date_raw)

    return CertResult(
        found=True,
        cert_type=cert_type,
        issue_date=issue_date,
        status=status,
        exam_name=exam_name,
        exam_date=exam_date,
        exam_center=exam_center,
        praedikat=praedikat,
        score_total=score_total,
        score_written=score_written,
        score_oral=score_oral,
    )
