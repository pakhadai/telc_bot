"""
handlers/start.py — /start + перший вибір мови (без ConversationHandler — сумісно з PTB per_*).
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

import storage
from i18n import t, LANG_NAMES


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


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

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
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"lang:{code}")]
        for code, name in LANG_NAMES.items()
    ])
    await update.message.reply_text(t("choose_lang", "ua"), reply_markup=keyboard)


async def on_first_lang_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Перший вибір мови (callback `lang:*`); зміна мови з меню — `setlang:*` у menu.py."""
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


start_handler = CommandHandler("start", cmd_start)
first_lang_handler = CallbackQueryHandler(on_first_lang_pick, pattern=r"^lang:")
