"""
test_api.py — перевірка API + парсера з реальними даними.

Запуск:  python test_api.py
"""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import aiohttp
from scraper.parser import parse_certificate_response

API_BASE = "https://results.telc.net/api/results"

PNR       = "4627704"
BIRTH_ISO = "1994-02-23"
DATE_ISO  = "2025-11-13"

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
        print("\n" + "="*60)
        print("FULL CERTIFICATE RESPONSE:")
        print(json.dumps(detail_data, indent=2, ensure_ascii=False))

        # ── Тест парсера ──────────────────────────────────────────────────────
        print("\n" + "="*60)
        print("PARSER OUTPUT:")
        result = parse_certificate_response(lookup_data, detail_data, cert_type, DATE_ISO)
        print(f"  found:        {result.found}")
        print(f"  cert_type:    {result.cert_type}")
        print(f"  status:       {result.status}")
        print(f"  exam_name:    {result.exam_name}")
        print(f"  exam_date:    {result.exam_date}")
        print(f"  issue_date:   {result.issue_date}")
        print(f"  exam_center:  {result.exam_center}")
        print(f"  praedikat:    {result.praedikat}")
        print(f"  score_total:  {result.score_total}")
        print(f"  score_written:{result.score_written}")
        print(f"  score_oral:   {result.score_oral}")

        # ── Симуляція Telegram повідомлення ───────────────────────────────────
        print("\n" + "="*60)
        print("TELEGRAM MESSAGE PREVIEW (UA):")
        from utils.formatting import format_result
        msg = format_result(PNR, result, "ua")
        print(msg)


if __name__ == "__main__":
    asyncio.run(main())
