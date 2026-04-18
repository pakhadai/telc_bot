"""
handlers/start.py — /start + вибір мови.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import storage
from i18n import t, LANG_NAMES

LANG_PICK = 0


def get_main_menu_markup(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_add", lang),       callback_data="menu:add"),
            InlineKeyboardButton(t("btn_list", lang),      callback_data="menu:list"),
        ],
        [
            InlineKeyboardButton(t("btn_check_all", lang), callback_data="menu:check_all"),
            InlineKeyboardButton(t("btn_lang", lang),      callback_data="menu:lang"),
        ],
    ])


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    user = storage.get_lang(chat_id)

    # Якщо мова вже збережена — одразу головне меню
    data = storage.get_all_users()
    if str(chat_id) in data and "lang" in data[str(chat_id)]:
        lang = storage.get_lang(chat_id)
        certs = storage.get_certs(chat_id)
        n = len(certs)
        text = t("welcome_back", lang, n=n) if n > 0 else t("welcome", lang)
        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_markup(lang),
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        return ConversationHandler.END

    # Перший запуск — вибір мови
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"lang:{code}")]
        for code, name in LANG_NAMES.items()
    ])
    await update.message.reply_text(t("choose_lang", "ua"), reply_markup=keyboard)
    return LANG_PICK


async def _lang_picked(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]
    storage.set_lang(query.message.chat_id, lang)
    await query.message.edit_text(
        t("welcome", lang),
        reply_markup=get_main_menu_markup(lang),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )
    return ConversationHandler.END


lang_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", cmd_start)],
    states={LANG_PICK: [CallbackQueryHandler(_lang_picked, pattern=r"^lang:")]},
    fallbacks=[],
    name="lang_conv",
    persistent=False,
)

start_handler = CommandHandler("start", cmd_start)
