import asyncio
import logging
import io
import requests
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BufferedInputFile
)

# ────────────────────────────────────────────────
TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"

# ID основной таблицы (для предыдущих кнопок)
MAIN_SPREADSHEET_ID = "1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA"
SINGLE_SHEET_GID = "1841691264"

# Новая таблица — планы от РУАД
PLANS_SPREADSHEET_ID = "1SPmkft_ZvZr4tmCBcmzN0AE7HPscy3aRwB82uqR34CU"

# Кнопки
BUTTON_FULL_REPORT      = "Отчет по зимним видам работ ❄️"
BUTTON_WORKERS_EXCEL    = "Количество дорожных рабочих для МТДИ 🧑‍🏭"
BUTTON_PLANS_EXCEL      = "Планы от РУАД 📋"

# Смещение для московского времени
MSK_OFFSET = timedelta(hours=3)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ────────────────────────────────────────────────
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


@dp.message(CommandStart())
async def start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_FULL_REPORT)],
            [KeyboardButton(text=BUTTON_WORKERS_EXCEL)],
            [KeyboardButton(text=BUTTON_PLANS_EXCEL)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(
        "Выберите нужный отчёт:\n\n"
        "❄️ — полный отчёт (Excel всей таблицы + PDF листа)\n"
        "🧑‍🏭 — только лист с данными по дорожным рабочим (Excel)\n"
        "📋 — планы от РУАД (вся таблица в Excel)",
        reply_markup=kb
    )


# ── Полный отчёт (Excel всей таблицы + PDF одного листа) ─────────────
@dp.message(F.text == BUTTON_FULL_REPORT)
async def send_full_report(message: Message):
    base_name, report_text = get_report_info()

    excel_filename = f"{base_name}.xlsx"
    pdf_filename   = f"{base_name}.pdf"

    await message.answer(report_text)

    # Excel всей основной таблицы
    url = f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=excel_filename),
            caption=None
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить Excel: {str(e)}")
        return

    # PDF конкретного листа
    pdf_url = (
        f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={SINGLE_SHEET_GID}&size=A3&portrait=false&fitw=true&"
        f"gridlines=false&printtitle=false&sheetnames=false&fzr=false"
    )
    try:
        r = requests.get(pdf_url, timeout=30)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=pdf_filename),
            caption=None
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить PDF: {str(e)}")


# ── Только лист gid=1841691264 в Excel ───────────────────────────────
@dp.message(F.text == BUTTON_WORKERS_EXCEL)
async def send_workers_excel(message: Message):
    filename = "Данные по дорожным рабочим.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{MAIN_SPREADSHEET_ID}/export?format=xlsx&gid={SINGLE_SHEET_GID}"

    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=filename),
            caption=None
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить данные по рабочим: {str(e)}")


# ── Планы от РУАД — вся таблица в Excel ──────────────────────────────
@dp.message(F.text == BUTTON_PLANS_EXCEL)
async def send_plans_excel(message: Message):
    filename = "ПЛАНЫ от РУАД.xlsx"
    url = f"https://docs.google.com/spreadsheets/d/{PLANS_SPREADSHEET_ID}/export?format=xlsx"

    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=filename),
            caption=None
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить планы от РУАД: {str(e)}")


# ────────────────────────────────────────────────
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    await dp.start_polling(
        bot,
        allowed_updates=["message"],
        drop_pending_updates=True
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")