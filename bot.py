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

# Кнопки
BUTTON_ALL_EXCEL = "📊 Все листы в один Excel"
BUTTON_PDF = "📄 PDF (отчёт)"

# Смещение для московского времени
MSK_OFFSET = timedelta(hours=3)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ────────────────────────────────────────────────
def get_report_filename() -> str:
    """Определяет имя файла по московскому времени (+3 к UTC)"""
    utc_now = datetime.now(timezone.utc)
    msk_now = utc_now + MSK_OFFSET
    hour = msk_now.hour
    
    if 18 <= hour or hour < 6:
        return "Отчет на 20:00.pdf"
    else:
        return "Отчет на 8:00.pdf"


@dp.message(CommandStart())
async def start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_ALL_EXCEL)],
            [KeyboardButton(text=BUTTON_PDF)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(
        "Выбери действие:\n\n"
        f"• {BUTTON_ALL_EXCEL} — вся таблица в одном .xlsx файле\n"
        f"• {BUTTON_PDF} — лист gid={PDF_GID} в PDF (A3, альбомная ориентация)",
        reply_markup=kb
    )


@dp.message(F.text == BUTTON_ALL_EXCEL)
async def export_all_excel(message: Message):
    export_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=xlsx"

    try:
        response = requests.get(export_url, timeout=40)
        response.raise_for_status()

        file_bytes = io.BytesIO(response.content)

        await message.answer_document(
            document=BufferedInputFile(
                file=file_bytes.getvalue(),
                filename="Все_листы.xlsx"
            ),
            caption="Вся таблица (все доступные листы)"
        )

    except requests.Timeout:
        await message.answer("⏳ Долго скачиваем файл. Попробуй ещё раз.")
    except requests.RequestException as e:
        await message.answer(f"❌ Не удалось скачать Excel: {str(e)}")
    except Exception as e:
        await message.answer(f"🚨 Ошибка: {str(e)}")


@dp.message(F.text == BUTTON_PDF)
async def export_pdf(message: Message):
    filename = get_report_filename()

    export_url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?"
        f"format=pdf&"
        f"gid={PDF_GID}&"
        f"size=A3&"             # A3
        f"portrait=false&"      # альбомная ориентация (landscape)
        f"fitw=true&"           # подгонка по ширине страницы
        f"gridlines=false&"     # без сетки
        f"printtitle=false&"    # без заголовка таблицы
        f"sheetnames=false&"    # без имени листа вверху
        f"fzr=false"            # без повторения замороженных строк
    )

    try:
        response = requests.get(export_url, timeout=30)
        response.raise_for_status()

        pdf_bytes = io.BytesIO(response.content)

        await message.answer_document(
            document=BufferedInputFile(
                file=pdf_bytes.getvalue(),
                filename=filename
            ),
            caption=f"{filename} (A3, альбомная, {MSK_OFFSET} к UTC)"
        )

    except requests.Timeout:
        await message.answer("⏳ Долго скачиваем PDF. Попробуй ещё раз.")
    except requests.RequestException as e:
        await message.answer(f"❌ Не удалось скачать PDF: {str(e)}\nПроверь доступ к таблице.")
    except Exception as e:
        await message.answer(f"🚨 Ошибка: {str(e)}")


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