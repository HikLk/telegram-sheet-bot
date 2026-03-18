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
# Настройки — замени TOKEN на реальный!
TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"  # ← твой токен сюда
URL = "https://docs.google.com/spreadsheets/d/1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA/export?format=xlsx&gid=1841691264"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ────────────────────────────────────────────────
@dp.message(CommandStart())
async def start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Выгрузить таблицу")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False  # клавиатура не пропадает после нажатия
    )
    await message.answer(
        "Привет! Нажми кнопку, чтобы получить таблицу:",
        reply_markup=kb
    )


@dp.message(F.text == "📊 Выгрузить таблицу")
async def export_sheet(message: Message):
    try:
        # Скачиваем файл
        response = requests.get(URL, timeout=20)
        response.raise_for_status()  # выбросит ошибку при 4xx/5xx

        # Отправляем в память, без сохранения на диск
        file_bytes = io.BytesIO(response.content)

        await message.answer_document(
            document=BufferedInputFile(
                file=file_bytes.getvalue(),
                filename="table.xlsx"
            ),
            caption="Вот твоя таблица из Google Sheets"
        )

    except requests.Timeout:
        await message.answer("⏳ Таймаут при скачивании таблицы. Попробуй позже.")
    except requests.RequestException as e:
        await message.answer(f"❌ Не удалось скачать таблицу: {str(e)}")
    except Exception as e:
        await message.answer(f"🚨 Произошла ошибка: {str(e)}")


# ────────────────────────────────────────────────
async def main():
    # Настройка логов
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger("aiogram")
    logger.info("Бот запускается...")

    # Запуск polling
    await dp.start_polling(
        bot,
        allowed_updates=["message"],
        drop_pending_updates=True  # очищаем очередь старых сообщений
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")