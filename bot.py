import asyncio
import logging
import io
import requests
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Text
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

TOKEN = "твой_токен_здесь"
URL = "https://docs.google.com/spreadsheets/d/1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA/export?format=xlsx&gid=1841691264"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📊 Выгрузить таблицу")]],
        resize_keyboard=True
    )
    await message.answer("Нажмите кнопку:", reply_markup=kb)

@dp.message(Text("📊 Выгрузить таблицу"))
async def export_sheet(message: Message):
    try:
        r = requests.get(URL, timeout=15)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(
                file=io.BytesIO(r.content).getvalue(),
                filename="table.xlsx"
            )
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())