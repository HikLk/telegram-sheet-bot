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

SPREADSHEET_ID = "1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA"

# PDF-лист
PDF_GID = "1841691264"

# Кнопка
BUTTON_REPORT = "Отчет по зимним видам работ ❄️"

# Смещение для московского времени
MSK_OFFSET = timedelta(hours=3)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ────────────────────────────────────────────────
def get_report_info():
    """Возвращает базовое имя файлов и текст периода в зависимости от MSK времени"""
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
            [KeyboardButton(text=BUTTON_REPORT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(
        "Нажмите кнопку ниже, чтобы получить отчёт ❄️",
        reply_markup=kb
    )


@dp.message(F.text == BUTTON_REPORT)
async def send_report(message: Message):
    base_name, report_text = get_report_info()

    excel_filename = f"{base_name}.xlsx"
    pdf_filename   = f"{base_name}.pdf"

    # 1. Отправляем текстовое сообщение первым
    await message.answer(report_text)

    # 2. Excel (вся таблица)
    excel_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx"

    try:
        excel_resp = requests.get(excel_url, timeout=40)
        excel_resp.raise_for_status()

        await message.answer_document(
            document=BufferedInputFile(
                file=excel_resp.content,
                filename=excel_filename
            ),
            caption=None  # без подписи
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить Excel: {str(e)}")
        return  # если Excel не скачался — дальше не пытаемся

    # 3. PDF (конкретный лист, A3 landscape)
    pdf_url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?"
        f"format=pdf&"
        f"gid={PDF_GID}&"
        f"size=A3&"
        f"portrait=false&"
        f"fitw=true&"
        f"gridlines=false&"
        f"printtitle=false&"
        f"sheetnames=false&"
        f"fzr=false"
    )

    try:
        pdf_resp = requests.get(pdf_url, timeout=30)
        pdf_resp.raise_for_status()

        await message.answer_document(
            document=BufferedInputFile(
                file=pdf_resp.content,
                filename=pdf_filename
            ),
            caption=None  # без подписи
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить PDF: {str(e)}")


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