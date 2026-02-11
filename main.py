import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
# ==================== КОНФИГУРАЦИЯ ====================

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Дата начала учебного года (понедельник первой нечётной недели)
# Подстрой под свой вуз!
SEMESTER_START = datetime.date(2025, 9, 1)

# ==================== РАСПИСАНИЕ ====================
# Структура: SCHEDULE[день_недели][четность] = [(время, тип, предмет, преподаватель, аудитория), ...]
# день_недели: 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт
# четность: "odd" = нечётная, "even" = чётная

SCHEDULE = {
    0: {  # Понедельник
        "odd": [
            ("9:00",  "лек", "ВЫСШ. МАТЕМАТ",      "Шаповалов Е.В.",  "451"),
            ("10:50", "пр",  "ЭК ПО ФК И СПОРТУ",  "",                ""),
            ("12:40", "пр",  "ИН. ЯЗ.",             "Николаева О.В.",  "326* Я"),
        ],
        "even": [
            ("9:00",  "лек", "ВЫСШ. МАТЕМАТ",      "Шаповалов Е.В.",  "451"),
            ("10:50", "пр",  "ЭК ПО ФК И СПОРТУ",  "",                ""),
            ("12:40", "пр",  "ИН. ЯЗ.",             "Николаева О.В.",  "326* Я"),
        ],
    },
    1: {  # Вторник
        "odd": [
            ("10:50", "лаб", "ХИМИЯ",         "Барунин А.А., Маслобоев Д.С.", "558*, 560*"),
            ("12:40", "пр",  "ВЫСШ. МАТЕМАТ", "Сахаров В.Ю.",                 "488"),
        ],
        "even": [
            ("10:50", "лаб", "ХИМИЯ",         "Барунин А.А., Маслобоев Д.С.", "558*, 560*"),
            ("12:40", "пр",  "ВЫСШ. МАТЕМАТ", "Сахаров В.Ю.",                 "488"),
        ],
    },
    2: {  # Среда
        "odd": [
            ("9:00",  "лек", "ИСТОРИЯ",           "Савинов М.А.",     "451"),
            ("10:50", "пр",  "ЭК ПО ФК И СПОРТУ", "",                 ""),
            ("12:40", "лек", "ИНФ.ТЕХН. И ПРОГР.", "Удовиченко А.С.",  "310"),
            ("14:55", "пр",  "ИСТОРИЯ",            "Охочинский Д.М.",  "488"),
        ],
        "even": [
            ("9:00",  "лек", "ИСТОРИЯ",           "Савинов М.А.",     "451"),
            ("10:50", "пр",  "ЭК ПО ФК И СПОРТУ", "",                 ""),
            ("12:40", "лек", "ИНФ.ТЕХН. И ПРОГР.", "Удовиченко А.С.",  "310"),
            ("14:55", "пр",  "ПРАВОВЕДЕНИЕ",       "Дмитриева А.П.",   "488"),
        ],
    },
    3: {  # Четверг
        "odd": [
            ("9:00",  "пр",  "ИНЖ.И КОМП. ГРАФ",    "Ракитская М.В., Ивкин С.П.", "505*"),
            ("10:50", "пр",  "ФИЗИКА",               "",                            "430*"),
            ("12:40", "лек", "ФИЗИКА",               "Комарова О.С.",               "327*"),
            ("14:55", "пр",  "ПСИХ-Я.ПРОФ.ДЕЯТ.",    "Алексеева Е.Н.",              "430*"),
        ],
        "even": [
            ("9:00",  "пр",  "ИНЖ.И КОМП. ГРАФ",    "Ракитская М.В., Ивкин С.П.", "505*"),
            ("10:50", "лаб", "ФИЗИКА",               "",                            "323*"),
            ("12:40", "лек", "ФИЗИКА",               "Комарова О.С.",               "327*"),
            ("14:55", "лек", "ХИМИЯ",                "Маслобоев Д.С.",              "331*"),
        ],
    },
    4: {  # Пятница
        "odd": [
            ("9:00",  "пр",  "ИНФ.ТЕХН. И ПРОГР.",   "Удовиченко А.С.", "ВЦ 280"),
            ("10:50", "лек", "ПРАВОВЕДЕНИЕ",          "Лебедь А.Л.",     "310"),
            ("12:40", "лек", "ПСИХ-Я.ПРОФ.ДЕЯТ.",     "Фомина А.П.",     "437*"),
        ],
        "even": [
            ("9:00",  "пр",  "ИНФ.ТЕХН. И ПРОГР.",   "Удовиченко А.С.", "ВЦ 280"),
        ],
    },
}

DAY_NAMES = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}

PAIR_NUMBERS = {
    "9:00":  "1️⃣",
    "10:50": "2️⃣",
    "12:40": "3️⃣",
    "14:55": "4️⃣",
    "16:40": "5️⃣",
    "18:25": "6️⃣",
}

TYPE_EMOJI = {
    "лек": "📗",
    "пр":  "📘",
    "лаб": "🔬",
}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_week_parity(date: datetime.date) -> str:
    """Определяет чётность недели по дате."""
    delta_days = (date - SEMESTER_START).days
    week_number = delta_days // 7  # 0-based номер недели от начала семестра
    # Неделя 0 = нечётная, 1 = чётная, 2 = нечётная, ...
    return "even" if week_number % 2 == 1 else "odd"


def parity_label(parity: str) -> str:
    return "нечётная" if parity == "odd" else "чётная"


def format_day_schedule(weekday: int, parity: str, date: datetime.date) -> str:
    """Формирует красивый текст расписания на один день."""
    day_name = DAY_NAMES[weekday]
    date_str = date.strftime("%d.%m.%Y")
    parity_str = parity_label(parity)

    if weekday > 4 or weekday not in SCHEDULE:
        return (
            f"📌 <b>{day_name}, {date_str}</b>\n"
            f"🔹 Неделя: <b>{parity_str}</b>\n\n"
            f"🎉 <i>Пар нет — выходной!</i>"
        )

    lessons = SCHEDULE[weekday].get(parity, [])

    if not lessons:
        return (
            f"📌 <b>{day_name}, {date_str}</b>\n"
            f"🔹 Неделя: <b>{parity_str}</b>\n\n"
            f"🎉 <i>В этот день пар нет!</i>"
        )

    lines = [
        f"📌 <b>{day_name}, {date_str}</b>",
        f"🔹 Неделя: <b>{parity_str}</b>",
        "",
    ]

    for time, ltype, subject, teacher, room in lessons:
        pair_num = PAIR_NUMBERS.get(time, "▪️")
        type_em = TYPE_EMOJI.get(ltype, "📄")

        line = f"{pair_num} <b>{time}</b> │ {type_em} <i>{ltype}</i>\n"
        line += f"    📚 <b>{subject}</b>\n"
        if teacher:
            line += f"    👤 {teacher}\n"
        if room:
            line += f"    🏫 Ауд. {room}\n"

        lines.append(line)

    return "\n".join(lines)


def get_main_keyboard():
    """Главная клавиатура бота."""
    keyboard = [
        ["📅 Расписание на сегодня"],
        ["📆 Расписание на завтра"],
        ["🗓️ Расписание на всю неделю"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ==================== ОБРАБОТЧИКИ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Привет!</b>\n\n"
        "Я бот расписания вашей группы.\n"
        "Выбери, что тебя интересует 👇",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


async def today_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    weekday = today.weekday()
    parity = get_week_parity(today)
    text = format_day_schedule(weekday, parity, today)

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_keyboard())


async def tomorrow_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    weekday = tomorrow.weekday()
    parity = get_week_parity(tomorrow)
    text = format_day_schedule(weekday, parity, tomorrow)

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=get_main_keyboard())


async def week_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today()
    # Определяем понедельник текущей недели
    monday = today - datetime.timedelta(days=today.weekday())
    parity = get_week_parity(today)

    header = (
        f"🗓️ <b>Расписание на всю неделю</b>\n"
        f"🔹 Неделя: <b>{parity_label(parity)}</b>\n"
        f"{'━' * 30}\n"
    )

    await update.message.reply_text(header, parse_mode="HTML")

    for day_offset in range(6):  # Пн-Сб
        day_date = monday + datetime.timedelta(days=day_offset)
        weekday = day_date.weekday()
        text = format_day_schedule(weekday, parity, day_date)

        # Выделяем текущий день
        if day_date == today:
            text = f"👉 <u>СЕГОДНЯ</u>\n\n{text}"

        await update.message.reply_text(text, parse_mode="HTML")

    await update.message.reply_text(
        "✅ <i>Расписание на неделю отправлено!</i>",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(),
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if "сегодня" in text.lower():
        await today_schedule(update, context)
    elif "завтра" in text.lower():
        await tomorrow_schedule(update, context)
    elif "неделю" in text.lower():
        await week_schedule(update, context)
    else:
        await update.message.reply_text(
            "🤔 Не понял. Используй кнопки ниже 👇",
            reply_markup=get_main_keyboard(),
        )


# ==================== ЗАПУСК ====================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
