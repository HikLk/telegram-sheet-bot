import logging
import io
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Text
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

# ────────────────────────────────────────────────
TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"          # ← замени на реальный
URL = "https://docs.google.com/spreadsheets/d/1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA/export?format=xlsx&gid=1841691264"

bot = Bot(token=TOKEN)
dp = Dispatcher()           # в aiogram 3 Bot передаётся только при запуске polling

# ────────────────────────────────────────────────
@dp.message(CommandStart())
async def start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Выгрузить таблицу")]
        ],
        resize_keyboard=True
    )
    await message.answer("Нажмите кнопку:", reply_markup=kb)


@dp.message(Text("📊 Выгрузить таблицу"))
async def export_sheet(message: Message):
    try:
        response = requests.get(URL, timeout=20)
        response.raise_for_status()  # выбросит исключение при 4xx/5xx

        file_bytes = io.BytesIO(response.content)

        await message.answer_document(
            document=BufferedInputFile(
                file=file_bytes.getvalue(),
                filename="table.xlsx"
            ),
            caption="Вот ваша таблица"
        )

    except requests.RequestException as e:
        await message.answer(f"Не удалось скачать таблицу: {str(e)}")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")


# ────────────────────────────────────────────────
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # можно добавить await bot.delete_webhook(drop_pending_updates=True)
    # если раньше использовался webhook и нужно очистить очередь

    await dp.start_polling(bot, allowed_updates=["message"])


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())