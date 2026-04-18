"""
handlers/tracking.py — ConversationHandler: додавання одного сертифіката.
Steps: ASK_LABEL → ASK_PNR → ASK_ISSUE_DATE → ASK_BIRTH → done
"""

from telegram import Update
from telegram.ext import (
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

import storage
from i18n import t
from utils.dates import is_valid_date, date_range_bounds
from config import DATE_SEARCH_RANGE

ASK_LABEL, ASK_PNR, ASK_ISSUE_DATE, ASK_BIRTH = range(4)


async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point — called from menu handler."""
    chat_id = update.effective_chat.id
    lang = storage.get_lang(chat_id)

    if not storage.can_add_cert(chat_id):
        await update.effective_message.reply_text(
            t("max_certs", lang, max=storage.MAX_CERTS)
        )
        return ConversationHandler.END

    await update.effective_message.reply_text(t("ask_label", lang), parse_mode="Markdown")
    return ASK_LABEL


async def got_label(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = storage.get_lang(update.effective_chat.id)
    label = update.message.text.strip()[:40]  # cap at 40 chars
    if not label:
        await update.message.reply_text(t("ask_label", lang), parse_mode="Markdown")
        return ASK_LABEL
    context.user_data["label"] = label
    await update.message.reply_text(t("ask_pnr", lang), parse_mode="Markdown")
    return ASK_PNR


async def got_pnr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = storage.get_lang(update.effective_chat.id)
    pnr = update.message.text.strip()
    if not pnr:
        await update.message.reply_text(t("ask_pnr", lang), parse_mode="Markdown")
        return ASK_PNR
    context.user_data["pnr"] = pnr
    await update.message.reply_text(t("ask_issue_date", lang), parse_mode="Markdown")
    return ASK_ISSUE_DATE


async def got_issue_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = storage.get_lang(update.effective_chat.id)
    txt = update.message.text.strip()
    if not is_valid_date(txt):
        await update.message.reply_text(t("bad_date", lang), parse_mode="Markdown")
        return ASK_ISSUE_DATE
    context.user_data["center_date"] = txt
    await update.message.reply_text(t("ask_birth", lang), parse_mode="Markdown")
    return ASK_BIRTH


async def got_birth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = storage.get_lang(update.effective_chat.id)
    txt = update.message.text.strip()
    if not is_valid_date(txt):
        await update.message.reply_text(t("bad_date", lang), parse_mode="Markdown")
        return ASK_BIRTH

    label  = context.user_data["label"]
    pnr    = context.user_data["pnr"]
    center = context.user_data["center_date"]
    cert   = storage.add_cert(update.effective_chat.id, label, pnr, center, txt)
    context.user_data.clear()

    start, end = date_range_bounds(center, DATE_SEARCH_RANGE)
    await update.message.reply_text(
        t("saved", lang, label=label, pnr=pnr, start=start, end=end, birth=txt),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = storage.get_lang(update.effective_chat.id)
    context.user_data.clear()
    await update.message.reply_text(t("cancelled", lang))
    return ConversationHandler.END


tracking_conv_handler = ConversationHandler(
    entry_points=[],   # triggered programmatically from menu
    states={
        ASK_LABEL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_label)],
        ASK_PNR:        [MessageHandler(filters.TEXT & ~filters.COMMAND, got_pnr)],
        ASK_ISSUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_issue_date)],
        ASK_BIRTH:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_birth)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    name="tracking_conv",
    persistent=False,
)
