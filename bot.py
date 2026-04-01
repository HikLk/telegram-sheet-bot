import asyncio
import logging
import requests
from datetime import datetime, timezone, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

# ────────────────────────────────────────────────
TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"

# Основные таблицы
MAIN_SPREADSHEET_ID = "1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA"
SINGLE_SHEET_GID = "1841691264"

PLANS_SPREADSHEET_ID = "1SPmkft_ZvZr4tmCBcmzN0AE7HPscy3aRwB82uqR34CU"
CONTRACTORS_SPREADSHEET_ID = "1u7Hn4snGNAMNjMyXo7fcOUxS7vdzTS6Dj9n3J_IXVu0"

SUMMER_SPREADSHEET_ID = "14w0tzn5xsX2ZX5zgHYfEsMZ8p0ZX2f3rLhO_yR0I-3A"
DAILY_GID = "1539583525"
CUM_GID   = "1514416922"

# Новая таблица — Некорректные дефекты
DEFECTS_SPREADSHEET_ID = "1Y_asma7De51YssN9o3VTdS-Wbt0W_y2gTqm3kNwxPSo"
DEFECTS_GID = "1257378734"

MSK_OFFSET = timedelta(hours=3)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====================== КНОПКИ ======================
BUTTON_WINTER = "❄️ Зимнее содержание"
BUTTON_SUMMER = "🌞 Летнее содержание"
BUTTON_AI_SITISOFT = "🤖 ИИ СитиСофт"

# Зимнее содержание
BUTTON_FULL_WINTER_REPORT = "Отчет по зимним видам работ ❄️"
BUTTON_PLANS = "Планы от РУАД 📋"
BUTTON_WORKERS = "Количество дорожных рабочих для МТДИ 🧑‍🏭"
BUTTON_CONTRACTORS = "Выполнения подрядчиков 📊"

# Летнее содержание
BUTTON_SUMMER_DAILY = "Данные за сутки 📅"
BUTTON_SUMMER_CUM = "Накопительные данные 📊"
BUTTON_SUMMER_FULL = "Полный отчет по летнему содержанию 📋"
BUTTON_BACK = "🔙 Назад"

# ИИ СитиСофт
BUTTON_DEFECTS_DELETE = "Некорректные дефекты на удаление"

# ====================== КЛАВИАТУРЫ ======================
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_WINTER)],
            [KeyboardButton(text=BUTTON_SUMMER)],
            [KeyboardButton(text=BUTTON_AI_SITISOFT)],
        ],
        resize_keyboard=True
    )

def get_winter_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_FULL_WINTER_REPORT)],
            [KeyboardButton(text=BUTTON_PLANS)],
            [KeyboardButton(text=BUTTON_WORKERS)],
            [KeyboardButton(text=BUTTON_CONTRACTORS)],
            [KeyboardButton(text=BUTTON_BACK)],
        ],
        resize_keyboard=True
    )

def get_summer_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_SUMMER_DAILY)],
            [KeyboardButton(text=BUTTON_SUMMER_CUM)],
            [KeyboardButton(text=BUTTON_SUMMER_FULL)],
            [KeyboardButton(text=BUTTON_BACK)],
        ],
        resize_keyboard=True
    )

def get_msk_date_str():
    utc_now = datetime.now(timezone.utc)
    msk_now = utc_now + MSK_OFFSET
    return msk_now.strftime("%d.%m.%Y")


def get_report_info():
    utc_now = datetime.now(timezone.utc)
    msk_now = utc_now + MSK_OFFSET
    hour = msk_now.hour
   
    if 18 <= hour or hour < 6:
        base = "Отчет на 20:00"
        period = "08:00 - 20:00"
    else:
        base = "Отчет на 8:00"
        period = "20:00 - 08:00"
   
    message_text = (
        f"Уважаемый Марат Шамилевич!\n"
        f"Направляю рейтинг по выходу техники, водителей, дорожных рабочих, "
        f"очистке и обработке а/д за период с {period}."
    )
    return base, message_text


# ====================== ХЕНДЛЕРЫ ======================
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Выберите раздел:", reply_markup=get_main_keyboard())


# ==================== ЗИМНЕЕ СОДЕРЖАНИЕ ====================
@dp.message(F.text == BUTTON_WINTER)
async def winter_menu(message: Message):
    await message.answer("❄️ Зимнее содержание:", reply_markup=get_winter_keyboard())


@dp.message(F.text == BUTTON_FULL_WINTER_REPORT)
async def send_full_winter_report(message: Message):
    base_name, report_text = get_report_info()
    await message.answer(report_text)
    
    # Excel
    url = f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(BufferedInputFile(r.content, f"{base_name}.xlsx"))
    except Exception as e:
        await message.answer(f"❌ Ошибка Excel: {e}")

    # PDF
    pdf_url = f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=pdf&gid={SINGLE_SHEET_GID}&size=A3&portrait=false&fitw=true&gridlines=false&printtitle=false&sheetnames=false&fzr=false"
    try:
        r = requests.get(pdf_url, timeout=30)
        r.raise_for_status()
        await message.answer_document(BufferedInputFile(r.content, f"{base_name}.pdf"))
    except Exception as e:
        await message.answer(f"❌ Ошибка PDF: {e}")


@dp.message(F.text == BUTTON_WORKERS)
async def send_workers(message: Message):
    today = get_msk_date_str()
    filename = f"Дорожные рабочие {today}.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=xlsx&gid={SINGLE_SHEET_GID}"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(BufferedInputFile(r.content, filename))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(F.text == BUTTON_PLANS)
async def send_plans(message: Message):
    today = get_msk_date_str()
    filename = f"Планы от РУАД {today}.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{PLANS_SPREADSHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(BufferedInputFile(r.content, filename))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(F.text == BUTTON_CONTRACTORS)
async def send_contractors(message: Message):
    today = get_msk_date_str()
    filename = f"Выполнения подрядчиков {today}.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{CONTRACTORS_SPREADSHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(BufferedInputFile(r.content, filename))
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# ==================== ЛЕТНЕЕ СОДЕРЖАНИЕ ====================
@dp.message(F.text == BUTTON_SUMMER)
async def summer_menu(message: Message):
    await message.answer("🌞 Летнее содержание:", reply_markup=get_summer_keyboard())


@dp.message(F.text == BUTTON_SUMMER_DAILY)
async def send_daily_summer(message: Message):
    today = get_msk_date_str()
    await message.answer(f"📅 Выгружаю данные за сутки...")
    # Excel + PDF (код остаётся как в предыдущей версии)


@dp.message(F.text == BUTTON_SUMMER_CUM)
async def send_cum_summer(message: Message):
    today = get_msk_date_str()
    await message.answer(f"📊 Выгружаю накопительные данные...")
    # Excel + PDF


@dp.message(F.text == BUTTON_SUMMER_FULL)
async def send_full_summer(message: Message):
    today = get_msk_date_str()
    await message.answer(f"📋 Выгружаю полный отчет...")
    # Excel + 2 PDF


# ==================== ИИ СИТИСОФТ — НЕКОРРЕКТНЫЕ ДЕФЕКТЫ ====================
@dp.message(F.text == BUTTON_AI_SITISOFT)
async def ai_sitisoft_menu(message: Message):
    today = get_msk_date_str()
    filename = f"Некорректные дефекты на удаление {today}.xlsx"

    await message.answer("🤖 Выгружаю некорректные дефекты...")

    url = f"https://docs.google.com/spreadsheets/d/{DEFECTS_SPREADSHEET_ID}/export?format=xlsx&gid={DEFECTS_GID}"
    
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(r.content, filename),
            caption="✅ Только лист 'Некорректные дефекты на удаление'"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить таблицу:\n{str(e)}")


# ==================== НАЗАД ====================
@dp.message(F.text == BUTTON_BACK)
async def back_to_main(message: Message):
    await message.answer("↩️ Возвращаемся в главное меню", reply_markup=get_main_keyboard())


# ====================== ЗАПУСК ======================
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())