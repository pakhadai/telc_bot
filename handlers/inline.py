"""
handlers/inline.py — inline queries (@bot у будь-якому чаті).
Показує список всіх відстежень із поточним статусом.
"""

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, ContextTypes

import storage
from i18n import t
from utils.dates import date_range_bounds
from config import DATE_SEARCH_RANGE


async def _inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query  = update.inline_query
    uid    = query.from_user.id
    lang   = storage.get_lang(uid)
    certs  = storage.get_certs(uid)

    if not certs:
        await query.answer([
            InlineQueryResultArticle(
                id="no_data", title="TELC Tracker",
                description=t("inline_no_data", lang),
                input_message_content=InputTextMessageContent(t("inline_no_data", lang)),
            )
        ], cache_time=10)
        return

    results = []
    for cert in certs:
        start, end = date_range_bounds(cert["center_date"], DATE_SEARCH_RANGE)
        status_key  = cert.get("last_status", "not_found")
        status_text = t(status_key, lang)
        icon = {"passed": "✅", "failed": "❌", "not_found": "🔄", "error": "⚠️"}.get(status_key, "🔄")

        summary = (
            f"{icon} *[{cert['id']}] {cert['label']}*\n"
            f"👤 `{cert['pnr']}`\n"
            f"📅 {start} – {end}\n"
            f"📊 {status_text}"
        )
        results.append(
            InlineQueryResultArticle(
                id=str(cert["id"]),
                title=f"{icon} [{cert['id']}] {cert['label']}  ({cert['pnr']})",
                description=status_text,
                input_message_content=InputTextMessageContent(summary, parse_mode="Markdown"),
            )
        )

    await query.answer(results, cache_time=30)


inline_handler = InlineQueryHandler(_inline_query)
