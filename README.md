# TELC Result Tracker Bot

<div align="center">
<img src="docs/images/logo.png" alt="TELC Result Tracker — перевірка сертифіката" width="200"/>
</div>

Telegram-бот для відстеження появи результату на [results.telc.net](https://results.telc.net/). Звертається до **публічних JSON API** порталу (lookup → картка сертифіката), без браузерного скрейпінгу.

**Призначення:** невелике особисте або «друзі й сім’я» навантаження; дані в **PostgreSQL** (якщо задано `DATABASE_URL`) або в **SQLite**. При першому старті порожньої БД виконується **одноразовий** імпорт з легасі-файлу `users_data.json` (після успіху файл перейменовується на `*.json.migrated`).

---

## Стек

| Компонент | Версія / примітка |
|-----------|-------------------|
| Python | ≥ 3.11 |
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | 21.x |
| [aiohttp](https://docs.aiohttp.org/) | HTTP-клієнт до TELC |
| [APScheduler](https://apscheduler.readthedocs.io/) | Планові перевірки |
| БД | SQLite (файл) або PostgreSQL через [psycopg](https://www.psycopg.org/) 3 |

Залежності: `requirements.txt`. Playwright **не** використовується.

---

## Можливості

- До **5** відстежень на користувача, власна мітка для кожного.
- Інтерфейс: **українська**, **німецька**, **англійська**.
- Планові перевірки **двічі на день** за календарем **Europe/Berlin** (за замовчуванням 09:00 і 17:00).
- Для кожної кандидатної дати Prüfung спочатку тип **`digital`**, потім **`paper`**.
- Після знаходження результату — збереження форматованого тексту в БД; повторний перегляд **з кешу** без запитів до TELC.
- Ручна перевірка з меню: **не частіше одного разу на календарний день** на користувача (той самий день за Berlin); автоперевірки на це правило не накладаються. Якщо всі записи лише показують збережений кеш — ліміт не витрачається.
- Опційно: [inline mode](https://core.telegram.org/bots/inline) (увімкнути в @BotFather).

---

## Структура репозиторію

```
telc_bot/
├── docs/
│   └── images/
│       └── logo.png     # Логотип для README
├── main.py              # Точка входу, PTB Application, post_init → scheduler
├── config.py            # Змінні середовища, константи, dataclass CertResult
├── i18n.py              # Рядки інтерфейсу (UA / DE / EN)
├── storage.py           # Користувачі, сертифікати, міграції SQLite/PG
├── scheduler.py         # APScheduler: цикл перевірок + health-check
├── requirements.txt
├── .env.example         # Приклад змінних для локального запуску
│
├── scraper/
│   ├── __init__.py
│   ├── runner.py        # aiohttp: lookup + certificate API
│   └── parser.py        # Розбір JSON відповіді порталу
│
├── handlers/
│   ├── start.py         # /start, головне меню
│   ├── tracking.py      # Діалог додавання відстеження
│   ├── menu.py          # Callback-меню (перевірки, деталі, мова)
│   ├── editing.py       # Редагування полів
│   └── inline.py        # Inline queries
│
└── utils/
    ├── dates.py         # Дати Prüfung для скану, Berlin «сьогодні»
    └── formatting.py    # CertResult → текст повідомлення
```

---

## Інтеграція з TELC

1. Користувач вводить **дату іспиту (Prüfung)** — не Datum der Ausstellung; дату видачі бот отримує з відповіді API після знаходження запису.
2. Для кожного запиту перебираються дати **Prüfung** у форматі `DD.MM.YYYY`, які підставляються в lookup URL (див. `scraper/runner.py`).
3. **Фаза 1** (поки `initial_sweep_done = false`): усі календарні дні **від дати іспиту до «сьогодні»** (Berlin), зверху обмежено `PHASE1_MAX_SPAN_DAYS`, щоб один прохід не розтягувався на роки.
4. Якщо за повний прохід фази 1 результату немає — у БД виставляється `initial_sweep_done`; далі **фаза 2**: лише останні **`ROLLING_SCAN_DAYS` + 1** днів до сьогодні включно, порядок від «сьогодні» назад (ковзне вікно).
5. Дні **пізніше за сьогодні** (Berlin) не запитуються.

Поля, які вводить користувач:

| Поле | Приклад |
|------|---------|
| Teilnehmernummer | `4627704` |
| Geburtsdatum | `23.02.1994` |
| Дата іспиту (Prüfung) | `27.10.2025` |

---

## Локальний запуск

```bash
python -m pip install -r requirements.txt
export BOT_TOKEN="..."   # або TELEGRAM_BOT_TOKEN
python main.py
```

Без `DATABASE_URL` створюється SQLite-файл (за замовчуванням `telc_bot.sqlite` у каталозі проєкту, див. `SQLITE_PATH`). Логи: `telc_bot.log`. Типові артефакти в `.gitignore`.

---

## Змінні середовища

| Змінна | Опис |
|--------|------|
| `BOT_TOKEN` або `TELEGRAM_BOT_TOKEN` | Токен бота від [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | Якщо задано — **PostgreSQL** (Railway підставляє `postgresql://...`; префікс `postgres://` нормалізується в коді) |
| `SQLITE_PATH` | Шлях до файлу SQLite, якщо Postgres не використовується |
| `ROLLING_SCAN_DAYS` | Довжина ковзного вікна фази 2 (за замовчуванням `7` → 8 календарних дат включно з сьогодні) |
| `PHASE1_MAX_SPAN_DAYS` | Максимальна кількість днів за один прохід фази 1 (за замовчуванням `400`) |
| `USERS_JSON_LEGACY` | Ім’я легасі JSON для одноразової міграції (за замовчуванням `users_data.json`) |

Константи в коді (`CHECK_TIMES`, `USER_DELAY_SECONDS`, `SCHEDULER_TIMEZONE`) за потреби змінюються у `config.py`.

---

## Планувальник і Telegram

Планувальник стартує в **`Application.post_init`**, а не до `run_polling()`, щоб уникнути конфлікту з asyncio event loop у PTB v21. Деталі — у коментарях у `main.py` та `scheduler.py`.

**Один процес на один `BOT_TOKEN`.** Два одночасні `getUpdates` для того самого бота дають `Conflict`. На хостингу тримай **одну репліку** сервісу; при підозрі на витік токена — `/revoke` у BotFather і оновлення змінної середовища.

---

## Деплой (приклад: Railway)

1. Підключити репозиторій, стартова команда: `python main.py`.
2. Додати **Variables**: `BOT_TOKEN` (або `TELEGRAM_BOT_TOKEN`).
3. **PostgreSQL:** створити плагін Postgres, у сервісі бота додати `DATABASE_URL` через **Reference** на змінну з БД.
4. **Альтернатива без Postgres:** volume (наприклад `/data`) і `SQLITE_PATH=/data/telc.sqlite`, щоб файл переживав redeploy.

Redis для цієї схеми даних не потрібен — використовуються реляційні таблиці в SQLite/PG.

---

## Приватність і обмеження

- Бот **не** є офіційним продуктом TELC; структура або доступність API можуть змінитися — тоді потрібні правки `runner.py` / `parser.py`.
- Не варто розгортати як публічний сервіс на сотні користувачів без окремого аналізу rate limits і відповідальності перед порталом.
- Тримай у таємниці токен бота та бекапи БД / SQLite.

---

## Ліцензія

Внутрішній / особистий проєкт — використання на власний розсуд.
