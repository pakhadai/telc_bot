# TELC Result Tracker Bot

<div align="center">
<img src="docs/images/logo.png" alt="TELC Result Tracker — перевірка сертифіката" width="200"/>
</div>

Telegram-бот для відстеження появи результату на [results.telc.net](https://results.telc.net/). Звертається до **публічних JSON API** порталу (lookup → картка сертифіката), без браузерного скрейпінгу.

**Призначення:** невелике особисте або «друзі й сім’я» навантаження; дані в **PostgreSQL** (якщо задано `DATABASE_URL`) або в **SQLite**. При першому старті порожньої БД виконується **одноразовий** імпорт з легасі-файлу `users_data.json` (після успіху файл перейменовується на `*.json.migrated`).

**Продакшен:** репозиторій розрахований на запуск у **Docker** на власному **VPS** (`Dockerfile`, `docker-compose.yml`). Оновлення коду з **GitHub** і автодеплой (CI/CD) підключаються окремо поверх цієї схеми.

---

## Стек

| Компонент | Версія / примітка |
|-----------|-------------------|
| Python | ≥ 3.11 |
| [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | 21.x |
| [aiohttp](https://docs.aiohttp.org/) | HTTP-клієнт до TELC |
| [APScheduler](https://apscheduler.readthedocs.io/) | Планові перевірки |
| БД | SQLite (файл) або PostgreSQL через [psycopg](https://www.psycopg.org/) 3 |
| Docker (VPS) | `Dockerfile` (multi-stage), `docker-compose.yml`: внутрішня **`telc-network`**, зовнішня **`npm_network`**, healthcheck, `restart: always` |

Залежності: `requirements.txt`. Playwright **не** використовується.

---

## Можливості

- До **5** відстежень на користувача, власна мітка для кожного.
- Інтерфейс: **українська**, **німецька**, **англійська**.
- Планові перевірки за календарем **Europe/Berlin**; розклад задається в `config.py` (`CHECK_TIMES`, за замовчуванням **15:00**).
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
├── Dockerfile           # Багатоетапна збірка: builder (venv + pip) → runtime
├── docker-compose.yml   # postgres + bot, telc-network + npm_network
├── .dockerignore
├── .github/workflows/   # ci.yml, deploy.yml (SCP + SSH на VPS)
├── .env.example         # Приклад змінних (не комітити .env)
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
| `DATABASE_URL` | Якщо задано — **PostgreSQL** (префікс `postgres://` нормалізується в коді). У штатному **docker-compose.yml** з локальним Postgres змінна **підставляється з compose** — у `.env` її не дублюйте, якщо не використовуєте власний сценарій |
| `POSTGRES_PASSWORD` | Пароль користувача БД для сервісу `postgres` у `docker-compose.yml` (на VPS обов’язково сильний унікальний пароль) |
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

## Розгортання на VPS (Docker)

Бот працює через **long polling** до Telegram: **вхідний** домен і **Nginx Proxy Manager** для самого бота **не потрібні** (на відміну від веб-сайтів). Достатньо вихідного HTTPS з VPS. Якщо пізніше перейдете на **webhooks**, тоді знадобиться публічний HTTPS URL і проксі в NPM.

### Вимоги на сервері

- Ubuntu з **Docker** і **Docker Compose** (plugin `docker compose`).
- Зовнішня мережа **npm_network** (як у стеку з Nginx Proxy Manager), щоб контейнери були в одній мережі з іншими сервісами:

  ```bash
  docker network inspect npm_network >/dev/null 2>&1 || docker network create npm_network
  ```

### Кроки

1. На VPS: каталог **`/root/apps/telc_bot`** (або інший; тоді змініть `target` у `.github/workflows/deploy.yml`).
2. Перший раз: `git clone` у цей каталог, `cp .env.example .env`, заповніть **`BOT_TOKEN`** (або `TELEGRAM_BOT_TOKEN`) та **`POSTGRES_PASSWORD`**. Далі деплой з GitHub копіює файли в той самий шлях — **`.env` лишайте лише на сервері**, не комітьте (workflow перевіряє наявність `.env` перед `docker compose`).
3. Збірка та запуск:

   ```bash
   cd /root/apps/telc_bot
   docker compose up -d --build
   ```

4. Логи: `docker compose logs -f bot`. Оновлення образу після змін у коді: знову `docker compose up -d --build`.

У `docker-compose.yml`: **`postgres`** лише в мережі **`telc-network`**; **`bot`** — у **`telc-network`** (зв’язок з БД) і **`npm_network`** (як у вашому фронтенд-стеку з NPM). Том **`postgres_data`**. Для бота `DATABASE_URL` підставляє compose (пароль **`POSTGRES_PASSWORD`** у `.env`).

Файл **`.env`** обов’язковий на VPS перед запуском. У `env_file` використано формат з `required: false` (Docker Compose **2.24+**); якщо плагін старіший — замініть блок на один рядок: `env_file: .env`.

### Зовнішня PostgreSQL

Якщо БД вже є на сервері: приберіть з `docker-compose.yml` сервіс **`postgres`**, том **`postgres_data`**, блок **`depends_on`** у сервісі **`bot`**, і задайте **`DATABASE_URL`** у `.env` на ваш кластер. Переконайтесь, що контейнер бота досягає хоста БД по мережі (часто — та сама `npm_network` або `extra_hosts`).

### SQLite в контейнері (без Postgres)

Якщо потрібен лише SQLite: не використовуйте штатний `docker-compose.yml` з Postgres; зіберіть образ (`docker build -t telc_bot .`) і запустіть контейнер з **`env_file` / `-e`**, без `DATABASE_URL`, з **`SQLITE_PATH`** на змонтований том (наприклад `-v telc_data:/data` і `SQLITE_PATH=/data/telc_bot.sqlite`).

### Безпека та один екземпляр

- Тримайте **`.env`** лише на сервері; не комітьте секрети.
- **Одна репліка** контейнера `bot` на один токен (див. розділ «Планувальник і Telegram»).
- SSH, фаєрвол і панелі керуйте згідно з вашою політикою на VPS (окремо від цього репозиторію).

### Оновлення з GitHub (CI/CD)

У репозиторії:

| Файл | Призначення |
|------|-------------|
| `.github/workflows/ci.yml` | На `push` / `pull_request` у **`main`**: Python 3.12, `pip install`, `compileall`, імпорт-перевірка, `docker compose config` (у CI тимчасово створюється мережа `npm_network`, якщо її немає). |
| `.github/workflows/deploy.yml` | На `push` у **`main`** і вручну (**workflow_dispatch**): **SCP** каталогу проєкту на VPS **`/root/apps/telc_bot`**, далі **SSH** — `docker compose config`, `build`, `up -d`, `docker image prune -f`. |

**Secrets** у GitHub (Settings → Secrets and variables → Actions): **`VPS_HOST`**, **`VPS_USER`**, **`VPS_PORT`**, **`VPS_SSH_KEY`** (приватний ключ SSH; збігається з форматом вашого pet-проєкту). На сервері має існувати **`/root/apps/telc_bot/.env`** з `BOT_TOKEN` і `POSTGRES_PASSWORD` (інший шлях — змініть `target` у кроці SCP і `cd` у скрипті deploy).

**Cloudflared** у цьому compose **не** додано: боту для long polling він не потрібен; за потреби тунель можна підняти окремим compose у тій самій `npm_network`.

---

## Інші середовища (Railway)

1. Підключити репозиторій, стартова команда: `python main.py`.
2. **Variables:** `BOT_TOKEN` (або `TELEGRAM_BOT_TOKEN`).
3. **PostgreSQL:** плагін Postgres, у сервісі бота `DATABASE_URL` через **Reference** на змінну з БД.
4. **Без Postgres:** volume (наприклад `/data`) і `SQLITE_PATH=/data/telc.sqlite`.

Redis для цієї схеми даних не потрібен — використовуються реляційні таблиці в SQLite/PG.

---

## Приватність і обмеження

- Бот **не** є офіційним продуктом TELC; структура або доступність API можуть змінитися — тоді потрібні правки `runner.py` / `parser.py`.
- Не варто розгортати як публічний сервіс на сотні користувачів без окремого аналізу rate limits і відповідальності перед порталом.
- Тримай у таємниці токен бота та бекапи БД / SQLite.

---

## Ліцензія

Внутрішній / особистий проєкт — використання на власний розсуд.
