# TELC Result Tracker Bot

Telegram-бот для відстеження результатів іспитів на [results.telc.net](https://results.telc.net/). Розрахований на **особисте користування** (ти й кілька друзів): дані зберігаються локально в JSON, без окремої бази даних.

**Стек:** Python ≥ 3.11 · [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) v21 · [aiohttp](https://docs.aiohttp.org/) · [APScheduler](https://apscheduler.readthedocs.io/)

**Як працює перевірка:** бот викликає **публічні JSON API** порталу TELC (lookup → деталі сертифіката), а не headless-браузер. Це легше для хостингу (Railway тощо) і швидше, ніж рендер SPA.

---

## Можливості

- Додавання кількох сертифікатів на користувача (до 5), власна мітка для кожного
- Мови інтерфейсу: українська, німецька, англійська
- Розклад перевірок **двічі на день** за часом Europe/Berlin (за замовчуванням 09:00 і 17:00)
- Спочатку шукається **цифровий** сертифікат, потім **паперовий**; для кожної дати в діапазоні
- Тест-режим: прев’ю повідомлення без запитів до TELC
- Опційно: inline-режим у Telegram (потрібно ввімкнути в @BotFather)

---

## Структура репозиторію

```
telc_bot/
├── main.py              # Точка входу, реєстрація хендлерів, post_init → scheduler
├── config.py            # Константи, dataclass CertResult
├── i18n.py              # Рядки UI (UA / DE / EN)
├── storage.py           # users_data.json (користувачі та сертифікати)
├── scheduler.py         # APScheduler + безпечна відправка в Telegram
├── requirements.txt
│
├── scraper/
│   ├── __init__.py      # Експорт check_telc()
│   ├── runner.py        # aiohttp: lookup + certificate API
│   └── parser.py        # Розбір JSON відповіді порталу
│
├── handlers/
│   ├── start.py         # /start, вибір мови
│   ├── tracking.py      # Діалог додавання сертифіката
│   ├── menu.py          # Inline-меню
│   └── inline.py        # Inline queries
│
└── utils/
    ├── dates.py         # Діапазон дат ±N днів, валідація
    └── formatting.py    # CertResult → текст повідомлення
```

---

## Логіка пошуку на TELC

1. Для кожної дати в інтервалі **«дата видачі з сертифіката» ± `DATE_SEARCH_RANGE` днів** (за замовчуванням ±21):
   - запит lookup: `Teilnehmernummer` + `Geburtsdatum` + поточна дата кандидата + тип `digital` або `paper`;
   - при успіху — другий запит за повними даними сертифіката й парсинг оцінок / статусу.
2. Якщо сертифіката в руках ще немає, можна вказати **орієнтовну** дату видачі — бот перебере сусідні дні в межах діапазону.

Поля з документа (або з листа від центру):

| Поле | Приклад |
|------|---------|
| Teilnehmernummer | `4627704` |
| Geburtsdatum | `23.02.1994` |
| Datum der Ausstellung | `13.11.2025` |

---

## Встановлення

### 1. Python 3.11+

```bash
pip install -r requirements.txt
```

Пакети: `python-telegram-bot`, `aiohttp`, `apscheduler`. **Playwright не потрібен.**

### 2. Токен бота

1. У [@BotFather](https://t.me/BotFather): `/newbot` → скопіювати токен.
2. Змінна середовища (Linux/macOS):

   ```bash
   export BOT_TOKEN="7123456789:AAH..."
   ```

   Windows (PowerShell):

   ```powershell
   $env:BOT_TOKEN = "7123456789:AAH..."
   ```

   У `config.py` токен читається з **`BOT_TOKEN`** або **`TELEGRAM_BOT_TOKEN`** (пробіли на початку/кінці обрізаються). Файл `.env.example` — підказка для локального запуску; на Railway змінні вказуються в **Variables**.

### 3. Запуск

```bash
python main.py
```

Файл `users_data.json` створиться після першого збереження даних. **Не коміть** його в git (вже в `.gitignore`).

### 4. Inline (опційно)

У BotFather: `/setinline` → обрати бота → placeholder, наприклад `telc`.

---

## Налаштування (`config.py`)

| Параметр | За замовчуванням | Опис |
|----------|------------------|------|
| `DATE_SEARCH_RANGE` | `21` | Днів ± від введеної дати видачі |
| `CHECK_TIMES` | `(9,0)`, `(17,0)` | Години перевірок (Europe/Berlin) |
| `USER_DELAY_SECONDS` | `2.0` | Пауза між користувачами під час планового циклу |

Логи: `telc_bot.log` (також у `.gitignore`).

---

## Планувальник і Telegram

Планувальник стартує в **`Application.post_init`**, а не до `run_polling()`, щоб уникнути конфлікту з asyncio event loop у PTB v21. Деталі — у коментарях у `main.py` та `scheduler.py`.

---

## Деплой (наприклад Railway)

1. Репозиторій на GitHub → New Project у [Railway](https://railway.app) з цього repo.
2. У **Variables** сервісу додай **`BOT_TOKEN`** = токен від @BotFather (ім’я змінної саме таке, без лапок у значенні). Альтернатива: **`TELEGRAM_BOT_TOKEN`**. Після зміни змінних натисни **Redeploy**.
3. Команда старту: `python main.py` (або `Procfile` з `worker: python main.py`).

Пам’ятай: **персистентний диск** — якщо `users_data.json` має зберігатися між деплоями, підключи volume або зовнішнє сховище; інакше після redeploy список сертифікатів обнулиться.

---

## Приватність і обмеження

- Бот **не** є офіційним продуктом TELC; API порталу можуть змінитися — тоді знадобиться оновлення `runner.py` / `parser.py`.
- Використовуй розумні інтервали між запитами; не варто масштабувати на сотні користувачів без окремого дизайну (rate limits, БД).
- Токен бота та `users_data.json` тримай приватними.

---

## GitHub: перший push

У каталозі проєкту вже є `git init` і перший commit на гілці `main`.

1. На [github.com/new](https://github.com/new) створи **порожній** репозиторій (наприклад `telc_bot`), **Private**, без README — щоб не було конфлікту з історією.
2. У PowerShell:

   ```powershell
   cd "C:\Users\Dmytro\Desktop\тест\telc_bot"
   git remote add origin https://github.com/ТВІЙ_НІК/telc_bot.git
   git push -u origin main
   ```

   Якщо `origin` уже був — `git remote set-url origin https://github.com/...`.

3. Авторизація: GitHub з 2021 зазвичай через **Personal Access Token** замість пароля, або [GitHub Desktop](https://desktop.github.com/), або встанови [GitHub CLI](https://cli.github.com/) (`gh auth login`) і тоді можна `gh repo create telc_bot --private --source=. --remote=origin --push`.

---

## Ліцензія

Приватний / особистий проєкт — використовуй на свій розсуд.
