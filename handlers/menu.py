"""
handlers/menu.py — всі InlineKeyboard callbacks.

Flows:
  menu:add          → tracking conversation
  menu:list         → список сертифікатів з кнопками
  menu:check:{id}   → перевірити конкретний
  menu:check_all    → перевірити всі
  menu:info:{id}    → деталі конкретного
  menu:test:{id}    → тест-режим для конкретного
  menu:del:{id}     → видалити конкретний
  menu:lang         → вибір мови
  setlang:{code}    → зберегти мову
"""

import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

import storage
from i18n import t, LANG_NAMES
from utils.dates import date_range_bounds, next_check_time
from utils.formatting import format_result, format_test_result
from scraper import check_telc
from config import DATE_SEARCH_RANGE


# ── Keyboard builders ─────────────────────────────────────────────────────────

def certs_list_markup(certs: list, lang: str) -> InlineKeyboardMarkup:
    """One row per cert + Add button at bottom."""
    rows = []
    for c in certs:
        status_icon = {"passed": "✅", "failed": "❌", "not_found": "🔄", "error": "⚠️"}.get(
            c.get("last_status", "not_found"), "🔄"
        )
        rows.append([
            InlineKeyboardButton(
                f"{status_icon} [{c['id']}] {c['label']}  ({c['pnr']})",
                callback_data=f"menu:info:{c['id']}"
            )
        ])
    rows.append([
        InlineKeyboardButton(t("btn_add", lang),      callback_data="menu:add"),
        InlineKeyboardButton(t("btn_check_all", lang), callback_data="menu:check_all"),
    ])
    return InlineKeyboardMarkup(rows)


def cert_detail_markup(cert_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_check", lang),  callback_data=f"menu:check:{cert_id}"),
            InlineKeyboardButton(t("btn_test", lang),   callback_data=f"menu:test:{cert_id}"),
        ],
        [
            InlineKeyboardButton(t("btn_delete", lang), callback_data=f"menu:del:{cert_id}"),
            InlineKeyboardButton(t("btn_back", lang),   callback_data="menu:list"),
        ],
    ])


# ── Main callback dispatcher ──────────────────────────────────────────────────

async def _handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts  = query.data.split(":")           # e.g. ["menu", "check", "2"]
    action = parts[1]
    chat_id = query.message.chat_id
    lang   = storage.get_lang(chat_id)

    # ── add ───────────────────────────────────────────────────────────────────
    if action == "add":
        from handlers.tracking import start_add, ASK_LABEL
        return await start_add(update, context)

    # ── list (main cert list) ─────────────────────────────────────────────────
    elif action == "list":
        certs = storage.get_certs(chat_id)
        if not certs:
            await query.message.reply_text(
                t("no_certs", lang),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(t("btn_add", lang), callback_data="menu:add")
                ]])
            )
            return
        await query.message.reply_text(
            t("cert_list_header", lang, n=len(certs), max=storage.MAX_CERTS),
            reply_markup=certs_list_markup(certs, lang),
            parse_mode="Markdown",
        )

    # ── info:{id} ─────────────────────────────────────────────────────────────
    elif action == "info":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        if not cert:
            await query.message.reply_text(t("cert_not_found", lang))
            return
        start, end = date_range_bounds(cert["center_date"], DATE_SEARCH_RANGE)
        status_key = cert.get("last_status", "not_found")
        last_check = cert.get("last_check") or "—"
        await query.message.reply_text(
            t("cert_detail", lang,
              id=cert["id"], label=cert["label"],
              pnr=cert["pnr"], start=start, end=end,
              birth=cert["birth"],
              status=t(status_key, lang),
              last_check=last_check,
              next_check=next_check_time()),
            reply_markup=cert_detail_markup(cert_id, lang),
            parse_mode="Markdown",
        )

    # ── check:{id} ────────────────────────────────────────────────────────────
    elif action == "check":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        if not cert:
            await query.message.reply_text(t("cert_not_found", lang))
            return
        loading = await query.message.reply_text(t("checking", lang))
        result = await check_telc(cert["pnr"], cert["center_date"], cert["birth"])
        if result.found:
            storage.update_cert_status(chat_id, cert_id, result.status)
        await loading.delete()
        await query.message.reply_text(
            f"*[{cert['id']}] {cert['label']}*\n" + format_result(cert["pnr"], result, lang),
            parse_mode="Markdown",
        )

    # ── check_all ─────────────────────────────────────────────────────────────
    elif action == "check_all":
        certs = storage.get_certs(chat_id)
        if not certs:
            await query.message.reply_text(t("no_certs", lang))
            return
        loading = await query.message.reply_text(
            t("checking_all", lang, n=len(certs))
        )
        for cert in certs:
            result = await check_telc(cert["pnr"], cert["center_date"], cert["birth"])
            if result.found:
                storage.update_cert_status(chat_id, cert["id"], result.status)
            await query.message.reply_text(
                f"*[{cert['id']}] {cert['label']}*\n" + format_result(cert["pnr"], result, lang),
                parse_mode="Markdown",
            )
        await loading.delete()

    # ── test:{id} ─────────────────────────────────────────────────────────────
    elif action == "test":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        pnr = cert["pnr"] if cert else "4627704"
        found = random.random() > 0.4
        label = cert["label"] if cert else "Test"
        await query.message.reply_text(
            f"*[{cert_id}] {label}*\n" + format_test_result(pnr, lang, found),
            parse_mode="Markdown",
        )

    # ── del:{id} ──────────────────────────────────────────────────────────────
    elif action == "del":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        label = cert["label"] if cert else "?"
        removed = storage.delete_cert(chat_id, cert_id)
        if removed:
            certs = storage.get_certs(chat_id)
            await query.message.reply_text(
                t("cert_deleted", lang, label=label),
                reply_markup=certs_list_markup(certs, lang) if certs else None,
            )
        else:
            await query.message.reply_text(t("cert_not_found", lang))

    # ── lang ──────────────────────────────────────────────────────────────────
    elif action == "lang":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(name, callback_data=f"setlang:{code}")]
            for code, name in LANG_NAMES.items()
        ])
        await query.message.reply_text(t("choose_lang", lang), reply_markup=keyboard)


async def _handle_setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    new_lang = query.data.split(":")[1]
    storage.set_lang(query.message.chat_id, new_lang)

    from handlers.start import get_main_menu_markup
    await query.message.edit_text(
        t("welcome", new_lang),
        reply_markup=get_main_menu_markup(new_lang),
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


menu_callback_handler   = CallbackQueryHandler(_handle_menu,    pattern=r"^menu:")
setlang_callback_handler = CallbackQueryHandler(_handle_setlang, pattern=r"^setlang:")
