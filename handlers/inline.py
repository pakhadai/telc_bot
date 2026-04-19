"""
handlers/inline.py — inline queries (@bot у будь-якому чаті).
Показує список всіх відстежень із поточним статусом.
"""

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler, ContextTypes

import storage
from i18n import t
from utils.dates import describe_cert_scan_range


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
        search_range = describe_cert_scan_range(
            cert["center_date"],
            lang,
            initial_sweep_done=bool(cert.get("initial_sweep_done")),
            completed_at=cert.get("completed_at"),
        )
        status_key  = cert.get("last_status", "not_found")
        status_text = t(status_key, lang)
        icon = {"passed": "✅", "failed": "❌", "not_found": "🔄", "error": "⚠️"}.get(status_key, "🔄")

        summary = (
            f"{icon} *[{cert['id']}] {cert['label']}*\n"
            f"👤 `{cert['pnr']}`\n"
            f"📅 {search_range}\n"
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
