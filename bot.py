import asyncio
import logging
import io
import requests

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

# PDF-лист (один и тот же для второй кнопки)
PDF_GID = "1841691264"
PDF_FILENAME = "Основной_лист.pdf"

# Кнопки
BUTTON_ALL_EXCEL = "📊 Все листы в один Excel"
BUTTON_PDF = "📄 PDF (gid=1841691264)"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ────────────────────────────────────────────────
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
        f"• {BUTTON_ALL_EXCEL} — выгрузит **всю таблицу** (все листы, включая Рейтинг ИТОГ и все РУАД) в один .xlsx файл\n"
        f"• {BUTTON_PDF} — выгрузит **только лист с gid={PDF_GID}** в PDF",
        reply_markup=kb
    )


@dp.message(F.text == BUTTON_ALL_EXCEL)
async def export_all_excel(message: Message):
    # Экспорт всей книги в .xlsx (все листы сразу)
    export_url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?"
        f"format=xlsx"
    )

    try:
        response = requests.get(export_url, timeout=40)
        response.raise_for_status()

        file_bytes = io.BytesIO(response.content)

        await message.answer_document(
            document=BufferedInputFile(
                file=file_bytes.getvalue(),
                filename="Все_листы.xlsx"
            ),
            caption="Вот вся таблица в одном Excel-файле (все доступные листы)"
        )

    except requests.Timeout:
        await message.answer("⏳ Долго скачиваем файл. Попробуй ещё раз.")
    except requests.RequestException as e:
        await message.answer(
            f"❌ Не удалось скачать Excel: {str(e)}\n"
            "Убедись, что таблица опубликована или доступна по ссылке (Anyone with the link)."
        )
    except Exception as e:
        await message.answer(f"🚨 Ошибка: {str(e)}")


@dp.message(F.text == BUTTON_PDF)
async def export_pdf(message: Message):
    # Экспорт конкретного листа в PDF
    export_url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?"
        f"format=pdf&"
        f"gid={PDF_GID}&"
        f"size=A4&"
        f"portrait=true&"
        f"fitw=true&"          # подгонка по ширине
        f"gridlines=false&"    # без сетки
        f"printtitle=false&"   # без заголовка
        f"sheetnames=false"    # без имени листа
    )

    try:
        response = requests.get(export_url, timeout=30)
        response.raise_for_status()

        pdf_bytes = io.BytesIO(response.content)

        await message.answer_document(
            document=BufferedInputFile(
                file=pdf_bytes.getvalue(),
                filename=PDF_FILENAME
            ),
            caption=f"PDF листа (gid={PDF_GID})"
        )

    except requests.Timeout:
        await message.answer("⏳ Долго скачиваем PDF. Попробуй ещё раз.")
    except requests.RequestException as e:
        await message.answer(
            f"❌ Не удалось скачать PDF: {str(e)}\n"
            "Проверь доступ к таблице (должна быть опубликована или 'Anyone with the link')."
        )
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