import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====================== КЛАВИАТУРА ======================
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❄️ Зимнее содержание")],
            [KeyboardButton(text="🌞 Летнее содержание")],
            [KeyboardButton(text="Выполнения подрядчиков 📊")],
            [KeyboardButton(text="🤖 ИИ СитиСофт")],
        ],
        resize_keyboard=True
    )

# ====================== ХЕНДЛЕРЫ ======================
@dp.message(CommandStart())
async def start(message: Message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    title = message.chat.title or "Личный чат"
    
    info = f"""
📍 <b>Информация о чате:</b>

🆔 <b>Chat ID:</b> <code>{chat_id}</code>
📌 <b>Тип чата:</b> {chat_type}
📝 <b>Название:</b> {title}

✅ Скопируй Chat ID выше и вставь в основной скрипт!
    """
    
    await message.answer(info, parse_mode="HTML")
    await message.answer("👋 Выберите раздел:", reply_markup=get_main_keyboard())


@dp.message(F.text == "🔙 Назад")
async def back(message: Message):
    await message.answer("↩️ Главное меню", reply_markup=get_main_keyboard())


# ====================== ЗАПУСК ======================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен. Напишите /start в нужной группе...")
    
    await dp.start_polling(bot, allowed_updates=["message"], drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())