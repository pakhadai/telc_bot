"""
handlers/editing.py — редагування полів сертифіката (ConversationHandler).
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import storage
from i18n import t
from utils.dates import is_valid_date

ASK_EDIT_VALUE = 0

_EDIT_FIELDS = frozenset({"label", "pnr", "center_date", "birth"})


def _field_title(field: str, lang: str) -> str:
    return t(f"edit_field_{field}", lang)


def _home_row(lang: str) -> list[InlineKeyboardButton]:
    btn = InlineKeyboardButton(
        t("btn_home", lang),
        callback_data="menu:home",
    )
    return [btn]


async def edit_field_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    cert_id = int(parts[2])
    field = parts[3]
    chat_id = update.effective_chat.id
    lang = storage.get_lang(chat_id)

    if field not in _EDIT_FIELDS:
        await query.message.reply_text(t("cert_not_found", lang))
        return ConversationHandler.END

    cert = storage.get_cert(chat_id, cert_id)
    if not cert:
        await query.message.reply_text(t("cert_not_found", lang))
        return ConversationHandler.END

    context.user_data["edit_cert_id"] = cert_id
    context.user_data["edit_field"] = field
    await query.message.reply_text(
        t("edit_ask_new_value", lang, field=_field_title(field, lang)),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([_home_row(lang)]),
    )
    return ASK_EDIT_VALUE


async def edit_got_value(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    chat_id = update.effective_chat.id
    lang = storage.get_lang(chat_id)
    field = context.user_data.get("edit_field")
    cert_id = context.user_data.get("edit_cert_id")
    if field not in _EDIT_FIELDS or not isinstance(cert_id, int):
        context.user_data.clear()
        return ConversationHandler.END

    raw = update.message.text.strip()
    if field in ("center_date", "birth"):
        if not is_valid_date(raw):
            await update.message.reply_text(
                t("bad_date", lang),
                parse_mode="Markdown",
            )
            return ASK_EDIT_VALUE
    elif field == "label":
        raw = raw[:40]
        if not raw:
            await update.message.reply_text(
                t("edit_ask_new_value", lang, field=_field_title(field, lang)),
                parse_mode="Markdown",
            )
            return ASK_EDIT_VALUE
    elif field == "pnr" and not raw:
        await update.message.reply_text(
            t("edit_ask_new_value", lang, field=_field_title(field, lang)),
            parse_mode="Markdown",
        )
        return ASK_EDIT_VALUE

    ok = storage.update_cert_field(chat_id, cert_id, field, raw)
    context.user_data.clear()
    if not ok:
        await update.message.reply_text(t("cert_not_found", lang))
        return ConversationHandler.END

    await update.message.reply_text(
        t("edit_saved", lang),
        reply_markup=InlineKeyboardMarkup([_home_row(lang)]),
    )
    return ConversationHandler.END


async def edit_cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    lang = storage.get_lang(update.effective_chat.id)
    context.user_data.clear()
    await update.message.reply_text(
        t("edit_cancelled", lang),
        reply_markup=InlineKeyboardMarkup([_home_row(lang)]),
    )
    return ConversationHandler.END


def build_edit_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_field_entry, pattern=r"^menu:editfield:")
        ],
        states={
            ASK_EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_got_value)
            ],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel)],
        name="edit_conv",
        persistent=False,
        conversation_timeout=300,
    )
