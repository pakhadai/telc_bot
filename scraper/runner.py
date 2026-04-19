"""
scraper/runner.py — REST API client для results.telc.net

Verified endpoints (з DevTools):
  Step 1 — Lookup:
    GET /api/results/loopkup/{pnr}/pruefung/{YYYY-MM-DD}/birthdate/{YYYY-MM-DD}?type=digital|paper
    Referer: https://results.telc.net/
    → 200: {attendeeId, examId, examinationInstituteId, isVirtualBadge, ...}
    → 404: not found

  Step 2 — Certificate detail:
    GET /api/results/certificate/{examinationInstituteId}/pruefungen/{examId}/teilnehmer/{attendeeId}
    Referer: https://results.telc.net/certificate/{examinationInstituteId}/{examId}/{attendeeId}
    → 200: {language, content: [...]}
"""

import asyncio
import logging
import random
from datetime import datetime

import aiohttp

from config import CertResult
from utils.dates import telc_pruefung_dates
from scraper.parser import parse_certificate_response

logger = logging.getLogger(__name__)

API_BASE = "https://results.telc.net/api/results"

# Базові заголовки — спільні для обох запитів
_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/18.5 Mobile/15E148 Safari/604.1 Edg/147.0.0.0"
    ),
    "Accept":           "application/json, text/plain, */*",
    "Accept-Encoding":  "gzip, deflate, br",
    "Accept-Language":  "de-DE,de;q=0.9,en;q=0.8",
    "DNT":              "1",
    "sec-fetch-dest":   "empty",
    "sec-fetch-mode":   "cors",
    "sec-fetch-site":   "same-origin",   # ← критично! браузер відправляє same-origin
    "Origin":           "https://results.telc.net",
}

# Referer для Step 1 (lookup) — головна сторінка
_REFERER_SEARCH = "https://results.telc.net/"

# Referer для Step 2 (certificate detail) — frontend route після lookup
def _referer_cert(examination_institute_id: str, exam_id: str, attendee_id: str) -> str:
    return f"https://results.telc.net/certificate/{examination_institute_id}/{exam_id}/{attendee_id}"

MAX_RETRIES     = 3
RETRY_BASE_WAIT = 2.0
DATE_DELAY      = 0.8


def _to_iso(date_ddmmyyyy: str) -> str:
    return datetime.strptime(date_ddmmyyyy, "%d.%m.%Y").strftime("%Y-%m-%d")


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
    referer: str,
) -> tuple[int, dict | None]:
    """
    GET запит з правильним Referer та retry.
    Повертає (status_code, json | None).
    """
    headers = {**_BASE_HEADERS, "Referer": referer}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                logger.debug("GET %s → %d", url[-80:], resp.status)

                if resp.status == 200:
                    return 200, await resp.json(content_type=None)
                if resp.status == 404:
                    return 404, None
                if resp.status in (401, 403):
                    logger.error("Auth error %d — headers may need update", resp.status)
                    return resp.status, None

                logger.warning("HTTP %d (attempt %d/%d): %s", resp.status, attempt, MAX_RETRIES, url[-60:])

        except asyncio.TimeoutError:
            logger.warning("Timeout (attempt %d/%d): %s", attempt, MAX_RETRIES, url[-60:])
        except aiohttp.ClientConnectionError as exc:
            logger.warning("Connection error (attempt %d/%d): %s", attempt, MAX_RETRIES, exc)
        except Exception as exc:
            logger.error("Unexpected error: %s", exc)
            return -1, None

        if attempt < MAX_RETRIES:
            wait = RETRY_BASE_WAIT * (2 ** (attempt - 1)) + random.uniform(0, 1)
            await asyncio.sleep(wait)

    return -1, None


async def _lookup(
    session: aiohttp.ClientSession,
    pnr: str,
    date_iso: str,
    birth_iso: str,
    cert_type: str,
) -> dict | None:
    """
    Step 1: loopkup endpoint.
    Referer = головна сторінка (як у браузері при першому запиті).
    """
    url = f"{API_BASE}/loopkup/{pnr}/pruefung/{date_iso}/birthdate/{birth_iso}?type={cert_type}"
    status, data = await _get_json(session, url, referer=_REFERER_SEARCH)
    if status == 200:
        logger.info("HIT  pnr=%s  type=%-7s  date=%s", pnr, cert_type, date_iso)
    return data


async def _get_certificate(
    session: aiohttp.ClientSession,
    examination_institute_id: str,
    exam_id: str,
    attendee_id: str,
) -> dict | None:
    """
    Step 2: certificate detail endpoint.
    Referer = frontend route (як у браузері після redirect).
    """
    url = (
        f"{API_BASE}/certificate/{examination_institute_id}"
        f"/pruefungen/{exam_id}"
        f"/teilnehmer/{attendee_id}"
    )
    # Referer точно відповідає тому що відправляє браузер після lookup
    referer = _referer_cert(examination_institute_id, exam_id, attendee_id)
    _, data = await _get_json(session, url, referer=referer)
    return data


async def check_telc(
    pnr: str,
    exam_date: str,
    birth: str,
    *,
    initial_sweep_done: bool = False,
) -> CertResult:
    """Публічний API — завжди повертає CertResult, ніколи не падає."""
    try:
        return await _run(pnr, exam_date, birth, initial_sweep_done=initial_sweep_done)
    except Exception as exc:
        logger.exception("Unexpected error in check_telc: %s", exc)
        return CertResult(found=False, status="error", error_message=str(exc))


async def _run(
    pnr: str,
    exam_date: str,
    birth: str,
    *,
    initial_sweep_done: bool,
) -> CertResult:
    birth_iso = _to_iso(birth)
    dates     = telc_pruefung_dates(exam_date, initial_sweep_done)
    checked   = 0

    # TCPConnector без keepalive — кожна сесія незалежна (менший ризик блокування)
    connector = aiohttp.TCPConnector(limit=2, ssl=True, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        for date_str in dates:
            checked += 1
            date_iso = _to_iso(date_str)

            for cert_type in ("digital", "paper"):
                lookup = await _lookup(session, pnr, date_iso, birth_iso, cert_type)
                if lookup is None:
                    continue

                detail = await _get_certificate(
                    session,
                    lookup.get("examinationInstituteId", ""),
                    lookup.get("examId", ""),
                    lookup.get("attendeeId", ""),
                )
                result = parse_certificate_response(lookup, detail, cert_type, date_str)
                result.dates_checked = checked
                return result

            await asyncio.sleep(DATE_DELAY + random.uniform(0, 0.3))

    return CertResult(found=False, status="not_found", dates_checked=checked)
