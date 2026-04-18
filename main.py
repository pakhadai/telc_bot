"""
main.py — entry point.

Ключовий фікс: scheduler стартує через post_init hook,
а не до run_polling() — це вирішує конфлікт event loop.
"""

import logging
import sys

from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    Application,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
    filters,
)

import storage

from config import (
    BOT_TOKEN,
    LOG_FILE,
    CHECK_TIMES,
    SCHEDULER_TIMEZONE,
    SQLITE_PATH,
    DATABASE_URL,
)
from handlers.start import (
    start_handler,
    first_lang_handler,
    menu_handler,
    fallback_text,
)
from handlers.tracking import (
    ASK_LABEL, ASK_PNR, ASK_ISSUE_DATE, ASK_BIRTH,
    got_label, got_pnr, got_issue_date, got_birth, cancel,
)
from handlers.menu import menu_callback_handler, setlang_callback_handler
from handlers.editing import build_edit_conversation
from handlers.inline import inline_handler
from scheduler import setup_scheduler

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
# Зменшити шум від бібліотек
for noisy in ("httpx", "httpcore", "apscheduler.executors", "telegram.ext.ExtBot"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def on_ptb_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, Conflict):
        logger.error(
            "Telegram Conflict: хтось інший уже викликає getUpdates з цим BOT_TOKEN. "
            "Перевір: (1) зупини локальний бот / інший хостинг; (2) у @BotFather /revoke "
            "і встав НОВИЙ токен лише в Railway; (3) один сервіс, одна репліка; "
            "(4) ніхто з друзів не запускає цей самий токен у себе."
        )
        return
    logger.error("Необроблена помилка PTB", exc_info=err)


def build_app() -> Application:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "BOT_TOKEN is not set. Add variable BOT_TOKEN (or TELEGRAM_BOT_TOKEN) "
            "in Railway → Variables / service settings, then redeploy. "
            "Local: export BOT_TOKEN=<token from @BotFather>"
        )
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_error_handler(on_ptb_error)

    # ── 1. /start + перший вибір мови (lang:* — лише старт; setlang:* у menu) ──
    app.add_handler(start_handler)
    app.add_handler(menu_handler)
    app.add_handler(first_lang_handler)

    # ── 2. Edit certificate (до add_conv — щоб menu:editfield не перехопив add) ─
    app.add_handler(build_edit_conversation())

    # ── 3. Add-tracking conversation (menu:* entry, крім editfield) ───────────
    #    Entry: menu:add callback → got_label → got_pnr → got_issue_date → got_birth
    add_conv = ConversationHandler(
        entry_points=[menu_callback_handler],   # menu:add sets state ASK_LABEL
        states={
            ASK_LABEL:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_label)],
            ASK_PNR:        [MessageHandler(filters.TEXT & ~filters.COMMAND, got_pnr)],
            ASK_ISSUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_issue_date)],
            ASK_BIRTH:      [MessageHandler(filters.TEXT & ~filters.COMMAND, got_birth)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="add_conv",
        persistent=False,
        conversation_timeout=300,   # 5 хв — якщо мовчить, скидаємо стан
    )
    app.add_handler(add_conv)

    # ── 4. Other callbacks ────────────────────────────────────────────────────
    app.add_handler(setlang_callback_handler)
    app.add_handler(inline_handler)

    # ── 5. Текст без активного сценарію — підказка + меню ────────────────────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text)
    )

    # ── 6. Scheduler через post_init ─────────────────────────────────────────
    #    post_init викликається ПІСЛЯ того як PTB запустив event loop,
    #    але ДО того як починається polling. Це єдиний безпечний спосіб
    #    стартувати APScheduler разом з asyncio.
    scheduler = setup_scheduler(app)

    async def _start_scheduler(application: Application) -> None:
        # Якщо колись увімкнули webhook — long polling не працюватиме без скидання.
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared (polling mode).")

        scheduler.start()
        times = " & ".join(f"{h:02d}:{m:02d}" for h, m in CHECK_TIMES)
        logger.info("Scheduler started. Checks: %s (%s)", times, SCHEDULER_TIMEZONE)

    async def _stop_scheduler(application: Application) -> None:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")

    app.post_init    = _start_scheduler
    app.post_shutdown = _stop_scheduler

    return app


def main() -> None:
    app = build_app()
    storage.init_db()
    if DATABASE_URL:
        logger.info("Storage: PostgreSQL (DATABASE_URL)")
    else:
        logger.info("Storage: SQLite — %s", SQLITE_PATH)
    logger.info("TELC Tracker Bot starting...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
