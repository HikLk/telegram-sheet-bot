import asyncio
import logging
import requests
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

import gspread
from google.oauth2.service_account import Credentials

# ====================== НАСТРОЙКИ ======================
TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"
TARGET_CHAT_ID = -4960002149
SERVICE_ACCOUNT_FILE = "service_account.json"

MAIN_SPREADSHEET_ID = "1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA"
SINGLE_SHEET_GID = "1841691264"

PLANS_SPREADSHEET_ID = "1SPmkft_ZvZr4tmCBcmzN0AE7HPscy3aRwB82uqR34CU"
CONTRACTORS_SPREADSHEET_ID = "1u7Hn4snGNAMNjMyXo7fcOUxS7vdzTS6Dj9n3J_IXVu0"

SUMMER_SPREADSHEET_ID = "14w0tzn5xsX2ZX5zgHYfEsMZ8p0ZX2f3rLhO_yR0I-3A"
DAILY_GID = "1539583525"
CUM_GID = "1514416922"

DEFECTS_SPREADSHEET_ID = "1Y_asma7De51YssN9o3VTdS-Wbt0W_y2gTqm3kNwxPSo"
DEFECTS_GID = "1257378734"

MSK_OFFSET = timedelta(hours=3)

bot = Bot(token=TOKEN)
dp = Dispatcher()

sent_cells = set()

# ====================== КЛАВИАТУРЫ ======================
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❄️ Зимнее содержание")],
            [KeyboardButton(text="🌞 Летнее содержание")],
            [KeyboardButton(text="📊 Выполнение подрядчиков")],
            [KeyboardButton(text="🤖 ИИ СитиСофт")],
        ],
        resize_keyboard=True
    )

def winter_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отчет по зимним видам работ ❄️")],
            [KeyboardButton(text="Планы от РУАД 📋")],
            [KeyboardButton(text="Количество дорожных рабочих 🧑‍🏭")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True
    )

def summer_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Данные за сутки 📅")],
            [KeyboardButton(text="Накопительные данные 📊")],
            [KeyboardButton(text="Полный отчет 📋")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True
    )

# ====================== УТИЛИТЫ ======================
def msk_now():
    return datetime.now(timezone.utc) + MSK_OFFSET

def today():
    return msk_now().strftime("%d.%m.%Y")

def report_info():
    hour = msk_now().hour
    if 18 <= hour or hour < 6:
        return "Отчет на 20:00", "08:00 - 20:00"
    return "Отчет на 8:00", "20:00 - 08:00"

def get_excel(url):
    r = requests.get(url, timeout=40)
    r.raise_for_status()
    return r.content

def get_pdf(url):
    r = requests.get(url, timeout=40)
    r.raise_for_status()
    return r.content

# ====================== МОНИТОРИНГ ======================
async def monitor():
    global last_reset_date
    print("🟢 Мониторинг активен. Автосброс sent_cells в 04:00 МСК")

    # Правильные scopes для работы с Google Sheets + Drive
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    while True:
        try:
            now = msk_now()
            today_date = now.date()

            # Автосброс в 04:00
            if now.hour == 4 and now.minute == 0 and last_reset_date != today_date:
                sent_cells.clear()
                last_reset_date = today_date
                print(f"✅ sent_cells сброшен в {now.strftime('%H:%M:%S')} МСК")

            # === НОВАЯ АВТОРИЗАЦИЯ ===
            creds = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=SCOPES
            )
            client = gspread.authorize(creds)

            # Проверка летнего отчёта
            sheet = client.open_by_key(SUMMER_SPREADSHEET_ID).get_worksheet_by_id(DAILY_GID)
            values = sheet.get_values("A1:A5")

            for i, row in enumerate(values):
                if row and str(row[0]).strip() == "✅":
                    cell = f"A{i+1}"

                    if cell not in sent_cells:
                        sent_cells.add(cell)

                        file = get_excel(
                            f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx"
                        )

                        await bot.send_document(
                            TARGET_CHAT_ID,
                            BufferedInputFile(file, f"Летний отчет {today()}.xlsx"),
                            caption=f"🔄 Автоотправка ({cell}) в {now.strftime('%H:%M')}"
                        )
                        print(f"✅ Отправлен файл по ячейке {cell}")
                    break

        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")

        await asyncio.sleep(30)
# ====================== ХЕНДЛЕРЫ ======================
@dp.message(CommandStart())
async def start(m: Message):
    await m.answer("Выберите раздел:", reply_markup=main_kb())

# ===== ЗИМА =====
@dp.message(F.text == "❄️ Зимнее содержание")
async def winter(m: Message):
    await m.answer("Зимнее содержание:", reply_markup=winter_kb())

@dp.message(F.text == "Отчет по зимним видам работ ❄️")
async def winter_report(m: Message):
    base, period = report_info()

    await m.answer(
        f"Уважаемый Марат Шамилевич!\n"
        f"Направляю данные за период {period}"
    )

    # Excel
    excel = get_excel(f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=xlsx")
    await m.answer_document(BufferedInputFile(excel, f"{base}.xlsx"))

    # PDF
    pdf = get_pdf(
        f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={SINGLE_SHEET_GID}&size=A3&portrait=false&fitw=true"
    )
    await m.answer_document(BufferedInputFile(pdf, f"{base}.pdf"))

@dp.message(F.text == "Планы от РУАД 📋")
async def plans(m: Message):
    file = get_excel(f"https://docs.google.com/spreadsheets/d/{PLANS_SPREADSHEET_ID}/export?format=xlsx")
    await m.answer_document(BufferedInputFile(file, f"Планы {today()}.xlsx"))

@dp.message(F.text == "Количество дорожных рабочих 🧑‍🏭")
async def workers(m: Message):
    file = get_excel(
        f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=xlsx&gid={SINGLE_SHEET_GID}"
    )
    await m.answer_document(BufferedInputFile(file, f"Рабочие {today()}.xlsx"))

# ===== ЛЕТО =====
@dp.message(F.text == "🌞 Летнее содержание")
async def summer(m: Message):
    await m.answer("Летнее содержание:", reply_markup=summer_kb())

@dp.message(F.text == "Данные за сутки 📅")
async def summer_daily(m: Message):
    await m.answer("📅 Выгружаю...")

    excel = get_excel(
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx&gid={DAILY_GID}"
    )
    await m.answer_document(BufferedInputFile(excel, f"Сутки {today()}.xlsx"))

    pdf = get_pdf(
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={DAILY_GID}&size=A3&portrait=false&fitw=true"
    )
    await m.answer_document(BufferedInputFile(pdf, f"Сутки {today()}.pdf"))

@dp.message(F.text == "Накопительные данные 📊")
async def summer_cum(m: Message):
    await m.answer("📊 Выгружаю...")

    excel = get_excel(
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx&gid={CUM_GID}"
    )
    await m.answer_document(BufferedInputFile(excel, f"Накопительные {today()}.xlsx"))

    pdf = get_pdf(
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={CUM_GID}&size=A3&portrait=false&fitw=true"
    )
    await m.answer_document(BufferedInputFile(pdf, f"Накопительные {today()}.pdf"))

@dp.message(F.text == "Полный отчет 📋")
async def summer_full(m: Message):
    await m.answer("📋 Выгружаю полный отчет...")

    excel = get_excel(
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx"
    )
    await m.answer_document(BufferedInputFile(excel, f"Полный отчет {today()}.xlsx"))

# ===== ПОДРЯДЧИКИ =====
@dp.message(F.text == "📊 Выполнение подрядчиков")
async def contractors(m: Message):
    file = get_excel(
        f"https://docs.google.com/spreadsheets/d/{CONTRACTORS_SPREADSHEET_ID}/export?format=xlsx"
    )
    await m.answer_document(BufferedInputFile(file, f"Подрядчики {today()}.xlsx"))

# ===== ИИ =====
@dp.message(F.text == "🤖 ИИ СитиСофт")
async def defects(m: Message):
    file = get_excel(
        f"https://docs.google.com/spreadsheets/d/{DEFECTS_SPREADSHEET_ID}/export?format=xlsx&gid={DEFECTS_GID}"
    )
    await m.answer_document(BufferedInputFile(file, f"Дефекты {today()}.xlsx"))

# ===== НАЗАД =====
@dp.message(F.text == "🔙 Назад")
async def back(m: Message):
    await m.answer("Главное меню", reply_markup=main_kb())

# ====================== ЗАПУСК ======================
async def main():
    logging.basicConfig(level=logging.INFO)

    asyncio.create_task(monitor())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())