"""
scheduler.py — правильна інтеграція APScheduler з python-telegram-bot v21.

Проблема: APScheduler.start() в async середовищі конфліктує з event loop.
Рішення: Application.post_init — scheduler стартує всередині event loop PTB.

Логіка сповіщень:
  - Є completed_at → повний пропуск (результат уже збережено, TELC не чіпаємо).
  - not_found → без повідомлення (не спамимо двічі на день).
  - Знайдено → save_cert_completion; у чат лише при першій знахідці або зміні статусу.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
from telegram.error import RetryAfter, TimedOut, NetworkError
from telegram.ext import Application

import storage
from scraper import check_telc
from utils.formatting import format_result
from config import CHECK_TIMES, SCHEDULER_TIMEZONE, USER_DELAY_SECONDS

logger = logging.getLogger(__name__)


async def _send_safe(bot: Bot, chat_id: int, text: str) -> None:
    """Send message з обробкою Telegram rate limits та мережевих помилок."""
    for attempt in range(3):
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
            return
        except RetryAfter as exc:
            wait = exc.retry_after + 1
            logger.warning("Rate limit hit for %s — waiting %ds", chat_id, wait)
            await asyncio.sleep(wait)
        except (TimedOut, NetworkError) as exc:
            logger.warning("Network error (attempt %d/3): %s", attempt + 1, exc)
            await asyncio.sleep(5 * (attempt + 1))
        except Exception as exc:
            logger.error("Failed to send to %s: %s", chat_id, exc)
            return


async def _run_all_checks(app: Application) -> None:
    users = storage.get_all_users()
    active = [(cid, u) for cid, u in users.items() if u.get("certs")]
    total_certs = sum(len(u["certs"]) for _, u in active)
    logger.info("Scheduled check: %d user(s), %d cert(s)", len(active), total_certs)

    for chat_id, user_data in active:
        lang = user_data.get("lang", "ua")
        for cert in user_data.get("certs", []):
            try:
                if cert.get("completed_at"):
                    logger.debug(
                        "Skip completed cert user=%s cert=%s (at %s)",
                        chat_id,
                        cert["id"],
                        (cert.get("completed_at") or "")[:10],
                    )
                    continue

                prev_status = cert.get("last_status", "not_found")

                result = await check_telc(
                    cert["pnr"],
                    cert["center_date"],
                    cert["birth"],
                    initial_sweep_done=bool(cert.get("initial_sweep_done")),
                )
                if not result.found:
                    storage.update_cert_status(int(chat_id), cert["id"], result.status)
                    if not cert.get("initial_sweep_done") and result.dates_checked > 0:
                        storage.set_initial_sweep_done(int(chat_id), cert["id"], True)
                    continue

                body = format_result(cert["pnr"], result, lang)
                storage.save_cert_completion(
                    int(chat_id), cert["id"], result.status, body
                )

                should_send = prev_status != result.status or prev_status in (
                    "not_found",
                    "error",
                )
                if should_send:
                    msg = f"*[{cert['id']}] {cert['label']}*\n" + body
                    await _send_safe(app.bot, int(chat_id), msg)

            except Exception as exc:
                logger.error("Check failed for user=%s cert=%s: %s", chat_id, cert["id"], exc)
                try:
                    storage.update_cert_status(int(chat_id), cert["id"], "error")
                except Exception:
                    pass

            await asyncio.sleep(USER_DELAY_SECONDS)


async def _health_check(app: Application) -> None:
    """Щогодинний health-check — логує що бот живий."""
    users = storage.get_all_users()
    active = sum(1 for u in users.values() if u.get("certs"))
    completed = sum(
        1
        for u in users.values()
        for c in u.get("certs", [])
        if c.get("completed_at")
    )
    logger.info(
        "Health-check OK — active users: %d, completed certs: %d",
        active,
        completed,
    )


def setup_scheduler(app: Application) -> AsyncIOScheduler:
    """
    Повертає scheduler (не запускає!).
    Запуск відбувається через post_init hook в main.py,
    всередині вже запущеного event loop від PTB.
    """
    scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)

    for h, m in CHECK_TIMES:
        scheduler.add_job(
            _run_all_checks,
            trigger="cron",
            hour=h, minute=m,
            args=[app],
            id=f"check_{h:02d}{m:02d}",
            replace_existing=True,
            misfire_grace_time=300,   # якщо бот був офлайн — виконати протягом 5 хв
        )

    # Health-check кожні 60 хвилин
    scheduler.add_job(
        _health_check,
        trigger="interval",
        minutes=60,
        args=[app],
        id="health_check",
        replace_existing=True,
    )

    return scheduler
