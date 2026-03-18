import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

URL = "https://docs.google.com/spreadsheets/d/1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA/export?format=xlsx&gid=1841691264"


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Выгрузить таблицу")
    await message.answer("Нажмите кнопку:", reply_markup=kb)


@dp.message_handler(lambda m: m.text == "📊 Выгрузить таблицу")
async def export_sheet(message: types.Message):

    r = requests.get(URL)

    with open("table.xlsx", "wb") as f:
        f.write(r.content)

    await message.answer_document(types.InputFile("table.xlsx"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp)