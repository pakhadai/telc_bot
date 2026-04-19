"""
handlers/menu.py — всі InlineKeyboard callbacks.

Flows:
  menu:add           → tracking conversation
  menu:list          → список сертифікатів з кнопками
  menu:home          → вітання + головне меню
  menu:check:{id}    → перевірити (кеш якщо completed_at)
  menu:check_all     → перевірити всі
  menu:info:{id}     → деталі конкретного
  menu:edit:{id}     → вибір поля для редагування
  menu:editfield:*   → ConversationHandler у handlers/editing.py
  menu:del:{id}      → підтвердження видалення
  menu:delconfirm:{id} → видалити
  menu:lang          → вибір мови
  setlang:{code}     → зберегти мову
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes

import storage
from i18n import t, LANG_NAMES
from utils.dates import describe_cert_scan_range, format_last_check, next_check_time
from utils.formatting import format_result
from scraper import check_telc


def home_keyboard_row(lang: str) -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")]


def home_reply_markup(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([home_keyboard_row(lang)])


# ── Keyboard builders ─────────────────────────────────────────────────────────

def certs_list_markup(certs: list, lang: str) -> InlineKeyboardMarkup:
    """Один рядок на сертифікат + додати / перевірити всі / додому."""
    rows = []
    for c in certs:
        status_icon = {"passed": "✅", "failed": "❌", "not_found": "🔄", "error": "⚠️"}.get(
            c.get("last_status", "not_found"), "🔄"
        )
        suffix = " 🔒" if c.get("completed_at") else ""
        rows.append([
            InlineKeyboardButton(
                f"{status_icon} [{c['id']}] {c['label']}  ({c['pnr']}){suffix}",
                callback_data=f"menu:info:{c['id']}"
            )
        ])
    rows.append([
        InlineKeyboardButton(t("btn_add", lang),      callback_data="menu:add"),
        InlineKeyboardButton(t("btn_check_all", lang), callback_data="menu:check_all"),
    ])
    rows.append(home_keyboard_row(lang))
    return InlineKeyboardMarkup(rows)


def cert_detail_markup(cert_id: int, lang: str, *, completed: bool = False) -> InlineKeyboardMarkup:
    check_caption = t("btn_view_saved", lang) if completed else t("btn_check", lang)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(check_caption, callback_data=f"menu:check:{cert_id}"),
        ],
        [
            InlineKeyboardButton(t("btn_edit", lang),   callback_data=f"menu:edit:{cert_id}"),
            InlineKeyboardButton(t("btn_delete", lang), callback_data=f"menu:del:{cert_id}"),
        ],
        [
            InlineKeyboardButton(t("btn_back", lang),   callback_data="menu:list"),
            InlineKeyboardButton(t("btn_home", lang),   callback_data="menu:home"),
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

    # ── home ──────────────────────────────────────────────────────────────────
    if action == "home":
        from handlers.start import get_main_menu_markup
        certs = storage.get_certs(chat_id)
        n = len(certs)
        text = t("welcome_back", lang, n=n) if n > 0 else t("welcome", lang)
        await query.message.reply_text(
            text,
            reply_markup=get_main_menu_markup(lang),
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        return

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
                    InlineKeyboardButton(t("btn_add", lang), callback_data="menu:add"),
                    InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home"),
                ]]),
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
        search_range = describe_cert_scan_range(
            cert["center_date"],
            lang,
            initial_sweep_done=bool(cert.get("initial_sweep_done")),
            completed_at=cert.get("completed_at"),
        )
        status_key = cert.get("last_status", "not_found")
        last_check = format_last_check(cert.get("last_check"))
        await query.message.reply_text(
            t("cert_detail", lang,
              id=cert["id"], label=cert["label"],
              pnr=cert["pnr"], search_range=search_range,
              birth=cert["birth"],
              status=t(status_key, lang),
              last_check=last_check,
              next_check=next_check_time()),
            reply_markup=cert_detail_markup(
                cert_id, lang, completed=bool(cert.get("completed_at"))
            ),
            parse_mode="Markdown",
        )

    # ── check:{id} ────────────────────────────────────────────────────────────
    elif action == "check":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        if not cert:
            await query.message.reply_text(t("cert_not_found", lang))
            return
        cached = cert.get("cached_result")
        if (
            cert.get("completed_at")
            and isinstance(cached, dict)
            and cached.get("formatted")
        ):
            body = cached["formatted"]
            await query.message.reply_text(
                f"*[{cert['id']}] {cert['label']}*\n" + body,
                parse_mode="Markdown",
                reply_markup=home_reply_markup(lang),
            )
            return
        loading = await query.message.reply_text(t("checking", lang))
        result = await check_telc(
            cert["pnr"],
            cert["center_date"],
            cert["birth"],
            initial_sweep_done=bool(cert.get("initial_sweep_done")),
        )
        if result.found:
            formatted = format_result(cert["pnr"], result, lang)
            storage.save_cert_completion(chat_id, cert_id, result.status, formatted)
        else:
            storage.update_cert_status(chat_id, cert_id, result.status)
            if not cert.get("initial_sweep_done") and result.dates_checked > 0:
                storage.set_initial_sweep_done(chat_id, cert_id, True)
        await loading.delete()
        await query.message.reply_text(
            f"*[{cert['id']}] {cert['label']}*\n" + format_result(cert["pnr"], result, lang),
            parse_mode="Markdown",
            reply_markup=home_reply_markup(lang),
        )

    # ── check_all ─────────────────────────────────────────────────────────────
    elif action == "check_all":
        certs = storage.get_certs(chat_id)
        if not certs:
            await query.message.reply_text(
                t("no_certs", lang),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(t("btn_add", lang), callback_data="menu:add"),
                    InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home"),
                ]]),
            )
            return
        loading = await query.message.reply_text(
            t("checking_all", lang, n=len(certs)),
        )
        for cert in certs:
            cached = cert.get("cached_result")
            if (
                cert.get("completed_at")
                and isinstance(cached, dict)
                and cached.get("formatted")
            ):
                body = cached["formatted"]
                await query.message.reply_text(
                    f"*[{cert['id']}] {cert['label']}*\n" + body,
                    parse_mode="Markdown",
                    reply_markup=home_reply_markup(lang),
                )
                continue
            result = await check_telc(
                cert["pnr"],
                cert["center_date"],
                cert["birth"],
                initial_sweep_done=bool(cert.get("initial_sweep_done")),
            )
            if result.found:
                formatted = format_result(cert["pnr"], result, lang)
                storage.save_cert_completion(chat_id, cert["id"], result.status, formatted)
            else:
                storage.update_cert_status(chat_id, cert["id"], result.status)
                if not cert.get("initial_sweep_done") and result.dates_checked > 0:
                    storage.set_initial_sweep_done(chat_id, cert["id"], True)
            await query.message.reply_text(
                f"*[{cert['id']}] {cert['label']}*\n" + format_result(cert["pnr"], result, lang),
                parse_mode="Markdown",
                reply_markup=home_reply_markup(lang),
            )
        await loading.delete()

    # ── edit:{id} ─────────────────────────────────────────────────────────────
    elif action == "edit":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        if not cert:
            await query.message.reply_text(t("cert_not_found", lang))
            return
        rows = [
            [
                InlineKeyboardButton(
                    t("edit_field_label", lang),
                    callback_data=f"menu:editfield:{cert_id}:label",
                )
            ],
            [
                InlineKeyboardButton(
                    t("edit_field_pnr", lang),
                    callback_data=f"menu:editfield:{cert_id}:pnr",
                )
            ],
            [
                InlineKeyboardButton(
                    t("edit_field_center_date", lang),
                    callback_data=f"menu:editfield:{cert_id}:center_date",
                )
            ],
            [
                InlineKeyboardButton(
                    t("edit_field_birth", lang),
                    callback_data=f"menu:editfield:{cert_id}:birth",
                )
            ],
            [
                InlineKeyboardButton(t("btn_back", lang), callback_data=f"menu:info:{cert_id}"),
                InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home"),
            ],
        ]
        await query.message.reply_text(
            t("edit_pick_field", lang),
            reply_markup=InlineKeyboardMarkup(rows),
        )

    # ── del:{id} ──────────────────────────────────────────────────────────────
    elif action == "del":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        if not cert:
            await query.message.reply_text(t("cert_not_found", lang))
            return
        label = cert["label"]
        await query.message.reply_text(
            t("confirm_delete", lang, label=label),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        t("btn_yes_delete", lang),
                        callback_data=f"menu:delconfirm:{cert_id}",
                    ),
                    InlineKeyboardButton(
                        t("btn_cancel_short", lang),
                        callback_data=f"menu:info:{cert_id}",
                    ),
                ],
                home_keyboard_row(lang),
            ]),
        )

    # ── delconfirm:{id} ───────────────────────────────────────────────────────
    elif action == "delconfirm":
        cert_id = int(parts[2])
        cert = storage.get_cert(chat_id, cert_id)
        label = cert["label"] if cert else "?"
        removed = storage.delete_cert(chat_id, cert_id) if cert else False
        if removed:
            certs = storage.get_certs(chat_id)
            markup = certs_list_markup(certs, lang) if certs else home_reply_markup(lang)
            await query.message.reply_text(
                t("cert_deleted", lang, label=label),
                reply_markup=markup,
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
