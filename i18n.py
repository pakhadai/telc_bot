"""
i18n.py — multilingual strings. UA / DE / EN.
"""

LANG_NAMES = {"ua": "🇺🇦 Українська", "de": "🇩🇪 Deutsch", "en": "🇬🇧 English"}

_S: dict[str, dict[str, str]] = {

    # ── Welcome ───────────────────────────────────────────────────────────────
    "choose_lang": {
        "ua": "🌐 Оберіть мову інтерфейсу:",
        "de": "🌐 Bitte wähle deine Sprache:",
        "en": "🌐 Please choose your language:",
    },
    "welcome": {
        "ua": (
            "👋 Привіт! Я відстежую результати *TELC* іспитів.\n\n"
            "🔍 Двічі на день перевіряю [results.telc.net](https://results.telc.net) "
            "і одразу повідомляю, коли результат з'явиться.\n"
            "Спочатку шукаю *цифровий* сертифікат, потім *паперовий*.\n\n"
            "Що робимо?"
        ),
        "de": (
            "👋 Hallo! Ich überwache deine *TELC*-Prüfungsergebnisse.\n\n"
            "🔍 Zweimal täglich prüfe ich [results.telc.net](https://results.telc.net) "
            "und benachrichtige dich sofort.\n"
            "Erst suche ich das *digitale*, dann das *Papierzertifikat*.\n\n"
            "Was möchtest du tun?"
        ),
        "en": (
            "👋 Hi! I track your *TELC* exam results.\n\n"
            "🔍 Twice a day I check [results.telc.net](https://results.telc.net) "
            "and notify you immediately.\n"
            "I try the *digital* certificate first, then the *paper* one.\n\n"
            "What would you like to do?"
        ),
    },
    "welcome_back": {
        "ua": "👋 З поверненням! У вас *{n}* активних відстежень.\nОберіть дію:",
        "de": "👋 Willkommen zurück! Du hast *{n}* aktive Trackings.\nWas möchtest du tun?",
        "en": "👋 Welcome back! You have *{n}* active trackings.\nWhat would you like to do?",
    },

    # ── Menu buttons ──────────────────────────────────────────────────────────
    "btn_add":       {"ua": "➕ Додати",          "de": "➕ Hinzufügen",      "en": "➕ Add"},
    "btn_list":      {"ua": "📋 Мої сертифікати", "de": "📋 Meine Zertifikate","en": "📋 My certs"},
    "btn_check_all": {"ua": "🔍 Перевірити всі",  "de": "🔍 Alle prüfen",     "en": "🔍 Check all"},
    "btn_check":     {"ua": "📊 Перевірити",      "de": "📊 Prüfen",          "en": "📊 Check"},
    "btn_view_saved": {
        "ua": "📋 Збережений результат",
        "de": "📋 Gespeichertes Ergebnis",
        "en": "📋 Saved result",
    },
    "btn_delete":    {"ua": "🗑 Видалити",        "de": "🗑 Löschen",         "en": "🗑 Delete"},
    "btn_back":      {"ua": "◀️ Назад",           "de": "◀️ Zurück",          "en": "◀️ Back"},
    "btn_lang":      {"ua": "🌐 Мова",            "de": "🌐 Sprache",         "en": "🌐 Language"},
    "btn_home": {
        "ua": "◀️ Головне меню",
        "de": "◀️ Hauptmenü",
        "en": "◀️ Main menu",
    },
    "btn_edit": {"ua": "✏️ Редагувати", "de": "✏️ Bearbeiten", "en": "✏️ Edit"},
    "btn_yes_delete": {
        "ua": "✅ Так, видалити",
        "de": "✅ Ja, löschen",
        "en": "✅ Yes, delete",
    },
    "btn_cancel_short": {
        "ua": "❌ Скасувати",
        "de": "❌ Abbrechen",
        "en": "❌ Cancel",
    },
    "cmd_menu_title": {
        "ua": "📱 Меню:",
        "de": "📱 Menü:",
        "en": "📱 Menu:",
    },
    "use_menu": {
        "ua": "Скористайтесь кнопками меню 👇",
        "de": "Bitte nutze das Menü 👇",
        "en": "Please use the menu buttons 👇",
    },
    "confirm_delete": {
        "ua": "Видалити відстеження *{label}*? Цю дію не можна скасувати після підтвердження.",
        "de": "Tracking *{label}* wirklich löschen? Das kann danach nicht rückgängig gemacht werden.",
        "en": "Delete tracking *{label}*? This cannot be undone after you confirm.",
    },
    "edit_pick_field": {
        "ua": "✏️ Оберіть поле для зміни:",
        "de": "✏️ Wähle ein Feld zum Ändern:",
        "en": "✏️ Choose a field to edit:",
    },
    "edit_field_label": {"ua": "Мітка", "de": "Bezeichnung", "en": "Label"},
    "edit_field_pnr": {"ua": "Teilnehmernummer (PNR)", "de": "Teilnehmernummer (PNR)", "en": "Participant number (PNR)"},
    "edit_field_center_date": {
        "ua": "Дата іспиту (Prüfungstag)",
        "de": "Prüfungstag (Examensdatum)",
        "en": "Exam date (Prüfung)",
    },
    "edit_field_birth": {"ua": "Geburtsdatum", "de": "Geburtsdatum", "en": "Date of birth"},
    "edit_ask_new_value": {
        "ua": "Введіть нове значення для: *{field}*",
        "de": "Neuen Wert eingeben für: *{field}*",
        "en": "Enter a new value for: *{field}*",
    },
    "edit_saved": {
        "ua": "✅ Збережено.",
        "de": "✅ Gespeichert.",
        "en": "✅ Saved.",
    },
    "edit_cancelled": {
        "ua": "❌ Редагування скасовано.",
        "de": "❌ Bearbeitung abgebrochen.",
        "en": "❌ Editing cancelled.",
    },

    # ── Certificate list ──────────────────────────────────────────────────────
    "cert_list_header": {
        "ua": "📋 *Ваші сертифікати* ({n}/{max}):\n\nНатисніть на сертифікат для деталей:",
        "de": "📋 *Deine Zertifikate* ({n}/{max}):\n\nKlicke auf ein Zertifikat für Details:",
        "en": "📋 *Your certificates* ({n}/{max}):\n\nTap a certificate for details:",
    },
    "no_certs": {
        "ua": "📭 У вас немає жодного відстеження. Додайте перший сертифікат:",
        "de": "📭 Du hast noch kein Tracking. Füge das erste Zertifikat hinzu:",
        "en": "📭 You have no tracking yet. Add your first certificate:",
    },
    "search_range_saved": {
        "ua": "збережений результат (Datum der Ausstellung та інше з кешу)",
        "de": "gespeichertes Ergebnis (Aus u. a. Cache)",
        "en": "saved result (issue date etc. from cache)",
    },
    "scan_exam_future": {
        "ua": "дата іспиту *{exam}* пізніше за сьогодні (*{today}*) — запити по датах ще не стартують",
        "de": "Prüfungsdatum *{exam}* liegt nach heute (*{today}*) — noch keine Datumsabfragen",
        "en": "exam *{exam}* is after today (*{today}*) — no date scans yet",
    },
    "scan_phase1_desc": {
        "ua": "фаза 1: від іспиту до сьогодні — *{start}* — *{end}*",
        "de": "Phase 1: Prüfung bis heute — *{start}* — *{end}*",
        "en": "phase 1: exam through today — *{start}* — *{end}*",
    },
    "scan_phase2_desc": {
        "ua": "фаза 2: останні дні — *{lo}* — *{hi}* (кожен запуск)",
        "de": "Phase 2: letzte Tage — *{lo}* — *{hi}* (pro Lauf)",
        "en": "phase 2: rolling window — *{lo}* — *{hi}* (each run)",
    },
    "scan_phase2_empty": {
        "ua": "фаза 2 (немає дат у вікні)",
        "de": "Phase 2 (keine Daten)",
        "en": "phase 2 (no dates)",
    },
    "cert_detail": {
        "ua": (
            "📄 *[{id}] {label}*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📅 Діапазон пошуку: {search_range}\n"
            "🎂 Geburtsdatum: `{birth}`\n\n"
            "📌 Останній статус: {status}\n"
            "🕐 Остання перевірка: {last_check}\n"
            "⏰ Наступна: {next_check}"
        ),
        "de": (
            "📄 *[{id}] {label}*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📅 Suchbereich: {search_range}\n"
            "🎂 Geburtsdatum: `{birth}`\n\n"
            "📌 Letzter Status: {status}\n"
            "🕐 Letzte Prüfung: {last_check}\n"
            "⏰ Nächste: {next_check}"
        ),
        "en": (
            "📄 *[{id}] {label}*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📅 Search range: {search_range}\n"
            "🎂 Geburtsdatum: `{birth}`\n\n"
            "📌 Last status: {status}\n"
            "🕐 Last check: {last_check}\n"
            "⏰ Next: {next_check}"
        ),
    },
    "cert_deleted": {
        "ua": "✅ Сертифікат *{label}* видалено.",
        "de": "✅ Zertifikat *{label}* gelöscht.",
        "en": "✅ Certificate *{label}* deleted.",
    },
    "cert_not_found": {
        "ua": "❌ Сертифікат не знайдено.",
        "de": "❌ Zertifikat nicht gefunden.",
        "en": "❌ Certificate not found.",
    },
    "max_certs": {
        "ua": "⚠️ Максимум {max} сертифікатів. Видаліть один перед додаванням.",
        "de": "⚠️ Maximum {max} Zertifikate. Lösche eines, bevor du ein neues hinzufügst.",
        "en": "⚠️ Maximum {max} certificates. Delete one before adding a new one.",
    },

    # ── Tracking conversation ─────────────────────────────────────────────────
    "ask_label": {
        "ua": (
            "📝 *Крок 1/4* — Назва\n\n"
            "Введіть коротку назву для цього сертифіката.\n"
            "Це лише для вас, щоб розрізняти записи.\n\n"
            "Приклади: `Dmytro B1`, `Мама C1`, `Test already received`"
        ),
        "de": (
            "📝 *Schritt 1/4* — Bezeichnung\n\n"
            "Gib einen kurzen Namen für dieses Zertifikat ein.\n"
            "Nur für dich, um die Einträge zu unterscheiden.\n\n"
            "Beispiele: `Max B2`, `Mama C1`, `Test erhalten`"
        ),
        "en": (
            "📝 *Step 1/4* — Label\n\n"
            "Enter a short name for this certificate.\n"
            "Just for you, to tell entries apart.\n\n"
            "Examples: `John B1`, `Mom C1`, `Test already received`"
        ),
    },
    "ask_pnr": {
        "ua": "📝 *Крок 2/4*\n\nВведіть *Teilnehmernummer* (з сертифіката, наприклад `4627704`):",
        "de": "📝 *Schritt 2/4*\n\nBitte gib deine *Teilnehmernummer* ein (z.B. `4627704`):",
        "en": "📝 *Step 2/4*\n\nEnter your *Teilnehmernummer* (e.g. `4627704`):",
    },
    "ask_issue_date": {
        "ua": (
            "📝 *Крок 3/4* — *дата іспиту (Prüfung)*\n\n"
            "Введіть *день здачі іспиту* (фактична дата Prüfung).\n"
            "💡 *Datum der Ausstellung* бот підставить сам, коли знайде запис на TELC.\n"
            "Спочатку перебір дат від іспиту до сьогодні; далі — лише останні 7 днів календаря.\n\n"
            "Формат: `ДД.ММ.РРРР` (наприклад `27.10.2025`)"
        ),
        "de": (
            "📝 *Schritt 3/4* — *Prüfungstag*\n\n"
            "Gib den *Tag der Prüfung* (tatsächliches Prüfungsdatum) ein.\n"
            "💡 *Datum der Ausstellung* holt der Bot, sobald ein Treffer da ist.\n"
            "Zuerst: alle Tage von der Prüfung bis heute; danach: rollierend die letzten 7 Tage.\n\n"
            "Format: `TT.MM.JJJJ` (z.B. `27.10.2025`)"
        ),
        "en": (
            "📝 *Step 3/4* — *exam date (Prüfung)*\n\n"
            "Enter the *exam day* (actual Prüfung date).\n"
            "💡 *Datum der Ausstellung* is filled in once the bot finds your record.\n"
            "First: every day from exam through today; then: rolling last 7 calendar days.\n\n"
            "Format: `DD.MM.YYYY` (e.g. `27.10.2025`)"
        ),
    },
    "ask_birth": {
        "ua": "📝 *Крок 4/4*\n\nВведіть *Geburtsdatum* (дата народження):\nФормат: `ДД.ММ.РРРР`",
        "de": "📝 *Schritt 4/4*\n\nBitte gib das *Geburtsdatum* ein:\nFormat: `TT.MM.JJJJ`",
        "en": "📝 *Step 4/4*\n\nEnter the *Geburtsdatum* (date of birth):\nFormat: `DD.MM.YYYY`",
    },
    "bad_date": {
        "ua": "❌ Невірний формат. Введіть дату як `ДД.ММ.РРРР`:",
        "de": "❌ Ungültiges Format. Bitte `TT.MM.JJJJ` verwenden:",
        "en": "❌ Invalid format. Please use `DD.MM.YYYY`:",
    },
    "saved": {
        "ua": (
            "✅ *Додано: {label}*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📅 Діапазон пошуку: {search_range}\n"
            "🎂 Geburtsdatum: `{birth}`\n\n"
            "⏰ Перевірки щодня о *09:00* та *17:00 CET*"
        ),
        "de": (
            "✅ *Hinzugefügt: {label}*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📅 Suchbereich: {search_range}\n"
            "🎂 Geburtsdatum: `{birth}`\n\n"
            "⏰ Prüfungen täglich um *09:00* und *17:00 Uhr (CET)*"
        ),
        "en": (
            "✅ *Added: {label}*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📅 Search range: {search_range}\n"
            "🎂 Geburtsdatum: `{birth}`\n\n"
            "⏰ Checks daily at *09:00* and *17:00 CET*"
        ),
    },

    # ── Result messages ───────────────────────────────────────────────────────
    "result_digital": {
        "ua": (
            "🎉 *ЦИФРОВИЙ СЕРТИФІКАТ ЗНАЙДЕНО!*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📜 Іспит: {exam_name}\n"
            "📅 Дата видачі: {issue_date}\n"
            "📊 Статус: {status}"
        ),
        "de": (
            "🎉 *DIGITALES ZERTIFIKAT GEFUNDEN!*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📜 Prüfung: {exam_name}\n"
            "📅 Ausstellungsdatum: {issue_date}\n"
            "📊 Status: {status}"
        ),
        "en": (
            "🎉 *DIGITAL CERTIFICATE FOUND!*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📜 Exam: {exam_name}\n"
            "📅 Issue date: {issue_date}\n"
            "📊 Status: {status}"
        ),
    },
    "result_paper": {
        "ua": (
            "🎉 *ПАПЕРОВИЙ СЕРТИФІКАТ ЗНАЙДЕНО!*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📜 Іспит: *{exam_name}*\n"
            "📅 Дата видачі: {issue_date}\n"
            "📆 Дата іспиту: {exam_date}\n"
            "🏫 Центр: {exam_center}\n\n"
            "📊 *Результати:*\n"
            "├ Загальний: {score_total}\n"
            "├ Письмова: {score_written}\n"
            "└ Усна: {score_oral}\n\n"
            "🏅 Prädikat: *{praedikat}*\n"
            "✅ Статус: {status}"
        ),
        "de": (
            "🎉 *PAPIERZERTIFIKAT GEFUNDEN!*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📜 Prüfung: *{exam_name}*\n"
            "📅 Ausstellungsdatum: {issue_date}\n"
            "📆 Prüfungsdatum: {exam_date}\n"
            "🏫 Prüfungszentrum: {exam_center}\n\n"
            "📊 *Ergebnisse:*\n"
            "├ Gesamt: {score_total}\n"
            "├ Schriftlich: {score_written}\n"
            "└ Mündlich: {score_oral}\n\n"
            "🏅 Prädikat: *{praedikat}*\n"
            "✅ Status: {status}"
        ),
        "en": (
            "🎉 *PAPER CERTIFICATE FOUND!*\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "📜 Exam: *{exam_name}*\n"
            "📅 Issue date: {issue_date}\n"
            "📆 Exam date: {exam_date}\n"
            "🏫 Exam centre: {exam_center}\n\n"
            "📊 *Results:*\n"
            "├ Total: {score_total}\n"
            "├ Written: {score_written}\n"
            "└ Oral: {score_oral}\n\n"
            "🏅 Prädikat: *{praedikat}*\n"
            "✅ Status: {status}"
        ),
    },
    "result_not_found": {
        "ua": (
            "📋 *Перевірка* — {time}\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "🔍 Перевірено дат: {n}\n"
            "📊 Статус: 🔄 Ще не опубліковано"
        ),
        "de": (
            "📋 *TELC-Prüfung* — {time}\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "🔍 Geprüfte Daten: {n}\n"
            "📊 Status: 🔄 Noch nicht veröffentlicht"
        ),
        "en": (
            "📋 *TELC Check* — {time}\n\n"
            "👤 Teilnehmernummer: `{pnr}`\n"
            "🔍 Dates checked: {n}\n"
            "📊 Status: 🔄 Not published yet"
        ),
    },

    # ── Status labels ─────────────────────────────────────────────────────────
    "passed":    {"ua": "✅ Bestanden (Складено)",         "de": "✅ Bestanden",        "en": "✅ Bestanden (Passed)"},
    "failed":    {"ua": "❌ Nicht bestanden (Не складено)", "de": "❌ Nicht bestanden", "en": "❌ Nicht bestanden (Failed)"},
    "not_found": {"ua": "🔄 Ще не знайдено",              "de": "🔄 Noch nicht gefunden","en": "🔄 Not found yet"},
    "error":     {"ua": "⚠️ Помилка перевірки",           "de": "⚠️ Fehler",          "en": "⚠️ Check error"},

    # ── Misc ──────────────────────────────────────────────────────────────────
    "checking": {
        "ua": "⏳ Перевіряю results.telc.net... (може зайняти до хвилини)",
        "de": "⏳ Ich prüfe results.telc.net... (kann bis zu einer Minute dauern)",
        "en": "⏳ Checking results.telc.net... (may take up to a minute)",
    },
    "checking_all": {
        "ua": "⏳ Перевіряю всі {n} сертифікатів...",
        "de": "⏳ Ich prüfe alle {n} Zertifikate...",
        "en": "⏳ Checking all {n} certificates...",
    },
    "cancelled": {
        "ua": "❌ Скасовано. /start щоб почати знову.",
        "de": "❌ Abgebrochen. /start zum Neustart.",
        "en": "❌ Cancelled. Type /start to restart.",
    },
    "inline_no_data": {
        "ua": "Немає відстежень — напишіть боту /start",
        "de": "Kein Tracking — schreibe dem Bot /start",
        "en": "No tracking — message the bot /start",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    lang = lang if lang in ("ua", "de", "en") else "ua"
    group = _S.get(key, {})
    text = group.get(lang) or group.get("en") or key
    return text.format(**kwargs) if kwargs else text
