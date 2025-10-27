
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import os
from dotenv import load_dotenv

load_dotenv()
# Токен бота (замени на свой)
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создаем клавиатуру с кнопками
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📆 Завтра")],
            [KeyboardButton(text="🗓️ Вся неделя"), KeyboardButton(text="ℹ️ О боте")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите команду..."
    )
    return keyboard

# Расписание занятий
SCHEDULE = {
    0: {  # Понедельник
        "9:00": [
            {"type": "лек", "subject": "ВЫСШ. МАТЕМАТ", "teacher": "Шаповалов Е.В.", "room": "451", "parity": "all"}
        ],
        "10:50": [
            {"type": "пр", "subject": "ЭК ПО ФК И СПОРТУ", "teacher": "", "room": "", "parity": "all"}
        ],
        "12:40": [
            {"type": "лек", "subject": "ВВЕД. В СПЕЦ", "teacher": "Охочинский М.Н.", "room": "318", "parity": "even"}
        ]
    },
    1: {  # Вторник
        "9:00": [
            {"type": "пр", "subject": "ИН. ЯЗ.", "teacher": "Николаева О.В.", "room": "317*", "parity": "all"}
        ],
        "10:50": [
            {"type": "пр", "subject": "ВЫСШ. МАТЕМАТ", "teacher": "Пелевина И.В.", "room": "418*", "parity": "all"}
        ]
    },
    2: {  # Среда
        "9:00": [
            {"type": "лек", "subject": "ИСТОРИЯ", "teacher": "Савинов М.А.", "room": "450", "parity": "all"}
        ],
        "10:50": [
            {"type": "пр", "subject": "ЭК ПО ФК И СПОРТУ", "teacher": "", "room": "", "parity": "all"}
        ],
        "12:40": [
            {"type": "лек", "subject": "ЭКОЛОГИЯ", "teacher": "Петров С.К.", "room": "316", "parity": "odd"},
            {"type": "лек", "subject": "ВВЕДЕНИЕ В ИТ", "teacher": "Щербакова Л.В.", "room": "314", "parity": "even"}
        ],
        "14:55": [
            {"type": "пр", "subject": "ВЫСШ. МАТЕМАТ", "teacher": "Пелевина И.В.", "room": "456", "parity": "all"}
        ]
    },
    3: {  # Четверг
        "9:00": [
            {"type": "лаб", "subject": "ЭКОЛОГИЯ", "teacher": "Лубянченко А.А.", "room": "384а", "parity": "odd"},
            {"type": "пр", "subject": "ВВЕДЕНИЕ В ИТ", "teacher": "Коваль А.А.", "room": "ВЦ 282", "parity": "even"}
        ],
        "10:50": [
            {"type": "пр", "subject": "ИСТОРИЯ", "teacher": "Охочинский Д.М.", "room": "456", "parity": "all"}
        ],
        "12:40": [
            {"type": "пр", "subject": "НАЧЕРТАТ. ГЕОМ", "teacher": "Ракитская М.В.", "room": "505*", "parity": "all"}
        ]
    },
    4: {  # Пятница
        "9:00": [
            {"type": "лек", "subject": "ФИЛОСОФИЯ", "teacher": "Вересова А.А.", "room": "429*", "parity": "odd"},
            {"type": "пр", "subject": "ФИЛОСОФИЯ", "teacher": "Вересова А.А.", "room": "418*", "parity": "even"}
        ],
        "10:50": [
            {"type": "лек", "subject": "НАЧЕРТАТ. ГЕОМ", "teacher": "Ракитская М.В.", "room": "429*", "parity": "all"}
        ],
        "12:40": [
            {"type": "пр", "subject": "ОСН РОС ГОС", "teacher": "Канатаев Д.В.", "room": "563*", "parity": "odd"},
            {"type": "лек", "subject": "ОСН РОС ГОС", "teacher": "Канатаев Д.В.", "room": "331*", "parity": "even"}
        ]
    },
    5: {  # Суббота
        "10:50": [
            {"type": "лек", "subject": "ФК И СПОРТ", "teacher": "Петров А.Б.", "room": "дистанционно", "parity": "odd"}
        ]
    }
}

def get_academic_year_start(current_year=None):
    """
    Определяет начало учебного года (1 сентября текущего года)
    """
    if current_year is None:
        current_year = datetime.now().year
    
    return datetime(current_year, 9, 1)

def get_week_parity(date=None):
    """
    Определяет четность недели относительно начала учебного года (1 сентября)
    Возвращает 'even' (четная) или 'odd' (нечетная)
    """
    if date is None:
        date = datetime.now()
    
    # Определяем начало учебного года
    current_year = date.year
    september_1 = get_academic_year_start(current_year)
    
    # Если текущая дата до 1 сентября, берем предыдущий учебный год
    if date < september_1:
        september_1 = get_academic_year_start(current_year - 1)
    
    # Вычисляем разницу в днях
    days_difference = (date - september_1).days
    
    # Вычисляем номер недели (начиная с 0)
    week_number = days_difference // 7
    
    # Определяем четность
    if week_number % 2 == 0:
        return "odd"  # нечетная
    else:
        return "even"  # четная

def get_russian_weekday(date):
    """
    Возвращает русское название дня недели
    """
    days = {
        0: "Понедельник",
        1: "Вторник", 
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье"
    }
    return days[date.weekday()]

def format_date(date):
    """
    Форматирует дату в русском стиле
    """
    months = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    
    return f"{date.day} {months[date.month]} {date.year} года"

def get_schedule_for_day(weekday, parity):
    """
    Возвращает расписание для указанного дня недели и четности
    """
    if weekday not in SCHEDULE:
        return None
    
    day_schedule = SCHEDULE[weekday]
    result = []
    
    # Сортируем время по порядку
    sorted_times = sorted(day_schedule.keys(), key=lambda x: datetime.strptime(x, "%H:%M"))
    
    for time in sorted_times:
        lessons = day_schedule[time]
        for lesson in lessons:
            if lesson["parity"] == "all" or lesson["parity"] == parity:
                result.append({
                    "time": time,
                    "type": lesson["type"],
                    "subject": lesson["subject"],
                    "teacher": lesson["teacher"],
                    "room": lesson["room"]
                })
    
    return result

def format_schedule(schedule, parity_russian):
    """
    Форматирует расписание в красивый текст
    """
    if not schedule:
        return f"🎉 В этот день пар нет! Отдыхайте!"
    
    result = f"📚 <b>Расписание ({parity_russian} неделя):</b>\n\n"
    
    for lesson in schedule:
        result += f"🕒 <b>{lesson['time']}</b>\n"
        result += f"   📖 {lesson['type']} {lesson['subject']}\n"
        if lesson['teacher']:
            result += f"   👨‍🏫 {lesson['teacher']}\n"
        if lesson['room']:
            result += f"   🏫 {lesson['room']}\n"
        result += "\n"
    
    return result

def get_current_week_dates():
    """
    Возвращает список дат на текущую неделю (понедельник - суббота)
    """
    today = datetime.now()
    # Находим понедельник текущей недели
    monday = today - timedelta(days=today.weekday())
    
    week_dates = []
    for i in range(6):  # понедельник - суббота
        week_dates.append(monday + timedelta(days=i))
    
    return week_dates

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start
    """
    welcome_text = (
        "👋 <b>Добро пожаловать в бот-расписание!</b>\n\n"
        "Я помогу вам узнать расписание пар на любой день.\n"
        "Используйте кнопки ниже для навигации:"
    )
    
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "📅 Сегодня")
async def cmd_today_button(message: types.Message):
    """
    Обработчик кнопки "Сегодня"
    """
    current_date = datetime.now()
    
    # Получаем данные
    weekday = current_date.weekday()
    weekday_russian = get_russian_weekday(current_date)
    formatted_date = format_date(current_date)
    week_parity = get_week_parity(current_date)
    parity_russian = "нечетная" if week_parity == "odd" else "четная"
    
    # Получаем расписание на сегодня
    today_schedule = get_schedule_for_day(weekday, week_parity)
    
    # Формируем ответ
    response = (
        f"📅 <b>Расписание на сегодня:</b>\n\n"
        f"📆 <b>День недели:</b> {weekday_russian}\n"
        f"🗓️ <b>Дата:</b> {formatted_date}\n"
        f"🎓 <b>Учебная неделя:</b> {parity_russian}\n"
        f"<i>(отсчет с 1 сентября)</i>\n\n"
    )
    
    if today_schedule:
        response += format_schedule(today_schedule, parity_russian)
    else:
        response += "🎉 Сегодня пар нет! Отдыхайте!"
    
    await message.answer(response, parse_mode="HTML")

@dp.message(lambda message: message.text == "📆 Завтра")
async def cmd_tomorrow_button(message: types.Message):
    """
    Обработчик кнопки "Завтра"
    """
    tomorrow_date = datetime.now() + timedelta(days=1)
    
    # Получаем данные
    weekday = tomorrow_date.weekday()
    weekday_russian = get_russian_weekday(tomorrow_date)
    formatted_date = format_date(tomorrow_date)
    week_parity = get_week_parity(tomorrow_date)
    parity_russian = "нечетная" if week_parity == "odd" else "четная"
    
    # Получаем расписание на завтра
    tomorrow_schedule = get_schedule_for_day(weekday, week_parity)
    
    # Формируем ответ
    response = (
        f"📅 <b>Расписание на завтра:</b>\n\n"
        f"📆 <b>День недели:</b> {weekday_russian}\n"
        f"🗓️ <b>Дата:</b> {formatted_date}\n"
        f"🎓 <b>Учебная неделя:</b> {parity_russian}\n\n"
    )
    
    if tomorrow_schedule:
        response += format_schedule(tomorrow_schedule, parity_russian)
    else:
        response += "🎉 Завтра пар нет! Отдыхайте!"
    
    await message.answer(response, parse_mode="HTML")

@dp.message(lambda message: message.text == "🗓️ Вся неделя")
async def cmd_week_button(message: types.Message):
    """
    Обработчик кнопки "Вся неделя"
    """
    current_date = datetime.now()
    week_parity = get_week_parity(current_date)
    parity_russian = "нечетная" if week_parity == "odd" else "четная"
    
    # Получаем даты текущей недели
    week_dates = get_current_week_dates()
    
    response = f"📚 <b>Расписание на неделю ({parity_russian} неделя):</b>\n\n"
    
    for i, date in enumerate(week_dates):
        day_schedule = get_schedule_for_day(i, week_parity)
        day_name = get_russian_weekday(date)
        formatted_day_date = format_date(date)
        
        response += f"📆 <b>{day_name} ({formatted_day_date}):</b>\n"
        
        if day_schedule:
            for lesson in day_schedule:
                room_info = f" - {lesson['room']}" if lesson['room'] else ""
                response += f"   🕒 {lesson['time']} - {lesson['type']} {lesson['subject']}{room_info}\n"
        else:
            response += f"   🎉 Пар нет\n"
        
        response += "\n"
    
    await message.answer(response, parse_mode="HTML")

@dp.message(lambda message: message.text == "ℹ️ О боте")
async def cmd_about_button(message: types.Message):
    """
    Обработчик кнопки "О боте"
    """
    about_text = (
        "🤖 <b>Информация о боте:</b>\n\n"
        "📚 <b>Бот-расписание</b>\n"
        "Автоматически определяет четность недели от 1 сентября\n\n"
        "🛠 <b>Функционал:</b>\n"
        "• 📅 Расписание на сегодня\n"
        "• 📆 Расписание на завтра\n"
        "• 🗓️ Расписание на всю неделю\n"
        "• 🔢 Автоопределение четности недели\n\n"
        "⚙️ <b>Техническая информация:</b>\n"
        "• Четность считается от 1 сентября\n"
        "• Расписание обновляется автоматически\n"
        "• Поддержка разных пар для четных/нечетных недель\n\n"
        "📞 Для связи с разработчиком используйте команды бота"
    )
    
    await message.answer(about_text, parse_mode="HTML")

@dp.message(Command("today"))
async def cmd_today(message: types.Message):
    """
    Резервная команда /today
    """
    await cmd_today_button(message)

@dp.message(Command("tomorrow"))
async def cmd_tomorrow(message: types.Message):
    """
    Резервная команда /tomorrow
    """
    await cmd_tomorrow_button(message)

@dp.message(Command("week"))
async def cmd_week(message: types.Message):
    """
    Резервная команда /week
    """
    await cmd_week_button(message)

@dp.message(Command("about"))
async def cmd_about(message: types.Message):
    """
    Резервная команда /about
    """
    await cmd_about_button(message)

# Обработчик любых других сообщений
@dp.message()
async def handle_other_messages(message: types.Message):
    """
    Обработчик любых других сообщений
    """
    help_text = (
        "❓ <b>Неизвестная команда</b>\n\n"
        "Используйте кнопки ниже для навигации:\n"
        "• <b>📅 Сегодня</b> - расписание на сегодня\n"
        "• <b>📆 Завтра</b> - расписание на завтра\n"
        "• <b>🗓️ Вся неделя</b> - расписание на неделю\n"
        "• <b>ℹ️ О боте</b> - информация о боте\n\n"
        "Или введите /start для перезапуска бота"
    )
    
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

async def main():
    """
    Основная функция запуска бота
    """
    logger.info("Бот запускается...")
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
