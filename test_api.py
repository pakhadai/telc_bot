"""
test_api.py — перевірка API + парсера з реальними даними.

Запуск:  python test_api.py

Останній блок друкує *точний* текст, який бот відправляє в чат після
«Перевірити» / «Перевірити всі» (handlers/menu.py: parse_mode="Markdown"):
  *[id] підпис*\n + format_result(...)
Підставте PREVIEW_CERT_* як у вашому записі в боті, щоб прев’ю збігалося 1:1.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import aiohttp
from scraper.parser import parse_certificate_response

API_BASE = "https://results.telc.net/api/results"

PNR       = "4736983"
BIRTH_ISO = "1994-02-23"
DATE_ISO  = "2026-05-08"

# Як у боті після додавання сертифіката (поле label та id у списку)
PREVIEW_CERT_ID    = 1
PREVIEW_CERT_LABEL = "Мій сертифікат"
PREVIEW_LANG       = "ua"  # ua | de | en

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9",
    "sec-fetch-site":  "same-origin",
    "sec-fetch-mode":  "cors",
    "sec-fetch-dest":  "empty",
    "Referer":         "https://results.telc.net/",
    "Origin":          "https://results.telc.net",
}


def build_telegram_check_message(cert_id: int, label: str, pnr: str, result, lang: str) -> str:
    """Той самий рядок, що menu.py передає в reply_text(..., parse_mode='Markdown')."""
    from utils.formatting import format_result

    body = format_result(pnr, result, lang)
    return f"*[{cert_id}] {label}*\n" + body


async def main():
    print("🔍 TELC API Test\n")

    async with aiohttp.ClientSession() as s:

        # ── Step 1: Lookup ────────────────────────────────────────────────────
        lookup_data = None
        cert_type   = None

        for ctype in ("digital", "paper"):
            url = f"{API_BASE}/loopkup/{PNR}/pruefung/{DATE_ISO}/birthdate/{BIRTH_ISO}?type={ctype}"
            print(f"Step 1 [{ctype}]: {url}")
            async with s.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                print(f"  → Status: {r.status}")
                if r.status == 200:
                    lookup_data = await r.json(content_type=None)
                    cert_type   = ctype
                    print(f"  → HIT! {json.dumps(lookup_data)}")
                    break
                else:
                    body = await r.text()
                    print(f"  → {body[:120]}")

        if not lookup_data:
            print("\n❌ Lookup failed for both types. Check PNR/date/birth.")
            return

        # ── Step 2: Certificate detail ────────────────────────────────────────
        eid = lookup_data["examinationInstituteId"]
        xid = lookup_data["examId"]
        aid = lookup_data["attendeeId"]

        cert_url    = f"{API_BASE}/certificate/{eid}/pruefungen/{xid}/teilnehmer/{aid}"
        cert_referer = f"https://results.telc.net/certificate/{eid}/{xid}/{aid}"

        print(f"\nStep 2: {cert_url}")
        async with s.get(
            cert_url,
            headers={**HEADERS, "Referer": cert_referer},
            timeout=aiohttp.ClientTimeout(total=15)
        ) as r:
            print(f"  → Status: {r.status}")
            if r.status != 200:
                print(f"  → Error: {await r.text()}")
                return
            detail_data = await r.json(content_type=None)

        # ── Повна відповідь ───────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("FULL CERTIFICATE RESPONSE:")
        print(json.dumps(detail_data, indent=2, ensure_ascii=False))

        # ── Парсер (коротко) ──────────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("PARSER (коротко):")
        result = parse_certificate_response(lookup_data, detail_data, cert_type, DATE_ISO)
        print(
            f"  found={result.found!r}  type={result.cert_type!r}  status={result.status!r}\n"
            f"  exam={result.exam_name!r}  exam_date={result.exam_date!r}  "
            f"issue={result.issue_date!r}\n"
            f"  scores: total={result.score_total!r} written={result.score_written!r} "
            f"oral={result.score_oral!r}"
        )

        # ── Як у Telegram після «Перевірити» (Markdown) ───────────────────────
        telegram_text = build_telegram_check_message(
            PREVIEW_CERT_ID,
            PREVIEW_CERT_LABEL,
            PNR,
            result,
            PREVIEW_LANG,
        )
        print("\n" + "=" * 60)
        print(
            "TELEGRAM — те саме, що reply_text(..., parse_mode='Markdown') "
            f"(lang={PREVIEW_LANG}):"
        )
        print("-" * 60)
        print(telegram_text)
        print("-" * 60)
        print(
            "У клієнті Telegram символи *…* стануть напівжирним/курсивом; "
            "у консолі Windows це залишається сирими символами Markdown."
        )


if __name__ == "__main__":
    asyncio.run(main())
