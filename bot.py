import asyncio
import logging
import requests
from datetime import datetime, timezone, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile

import gspread
from google.oauth2.service_account import Credentials
from collections import defaultdict

# ====================== НАСТРОЙКИ ======================
TOKEN = "8690731819:AAEN01HV4FxQ2gqTzVQQz02G58Q01Mi5SpQ"
TARGET_CHAT_ID = -4960002149   # ← Чат "Эксплуатация"

# ID таблиц
MAIN_SPREADSHEET_ID = "1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA"
SINGLE_SHEET_GID = "1841691264"
PLANS_SPREADSHEET_ID = "1SPmkft_ZvZr4tmCBcmzN0AE7HPscy3aRwB82uqR34CU"
CONTRACTORS_SPREADSHEET_ID = "1u7Hn4snGNAMNjMyXo7fcOUxS7vdzTS6Dj9n3J_IXVu0"
SUMMER_SPREADSHEET_ID = "14w0tzn5xsX2ZX5zgHYfEsMZ8p0ZX2f3rLhO_yR0I-3A"
DAILY_GID = "1539583525"
CUM_GID = "1514416922"
DEFECTS_SPREADSHEET_ID = "1Y_asma7De51YssN9o3VTdS-Wbt0W_y2gTqm3kNwxPSo"
DEFECTS_GID = "1257378734"

# Мониторинг
SERVICE_ACCOUNT_FILE = "service_account.json"
TRIGGER_VALUE = "✅"
sent_cells = set()

MSK_OFFSET = timedelta(hours=3)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====================== КЛАВИАТУРЫ ======================
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

def get_winter_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отчет по зимним видам работ ❄️")],
            [KeyboardButton(text="Планы от РУАД 📋")],
            [KeyboardButton(text="Количество дорожных рабочих для МТДИ 🧑‍🏭")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True
    )

def get_summer_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Данные за сутки 📅")],
            [KeyboardButton(text="Накопительные данные 📊")],
            [KeyboardButton(text="Полный отчет по летнему содержанию 📋")],
            [KeyboardButton(text="🔙 Назад")],
        ],
        resize_keyboard=True
    )

# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================
def get_msk_date_str():
    return (datetime.now(timezone.utc) + MSK_OFFSET).strftime("%d.%m.%Y")

# ====================== АВТОМАТИЧЕСКАЯ ОТПРАВКА ======================
async def check_and_send_reports():
    while True:
        try:
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
            client = gspread.authorize(creds)
            
            # Проверяем лист "Данные за сутки"
            sheet = client.open_by_key(SUMMER_SPREADSHEET_ID).get_worksheet_by_id(DAILY_GID)
            values = sheet.get_values("A1:A10")
            
            for i, row in enumerate(values):
                if row and str(row[0]).strip() == TRIGGER_VALUE:
                    cell = f"A{i+1}"
                    if cell not in sent_cells:
                        sent_cells.add(cell)
                        today = get_msk_date_str()
                        
                        # Выгружаем ПОЛНЫЙ ОТЧЁТ ЛЕТНЕГО СОДЕРЖАНИЯ
                        url = f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx"
                        r = requests.get(url, timeout=40)
                        r.raise_for_status()
                        
                        # Отправляем ТОЛЬКО в группу "Эксплуатация"
                        try:
                            await bot.send_document(
                                chat_id=TARGET_CHAT_ID,
                                document=BufferedInputFile(r.content, f"Полный отчет летнее содержание {today}.xlsx"),
                                caption=f"🔄 Автоматическая отправка\nПолный отчёт летнего содержания\nГалочка в {cell}"
                            )
                            print(f"✅ Отчёт отправлен в группу Эксплуатация")
                        except Exception as e:
                            logging.error(f"Ошибка отправки: {e}")
        except Exception as e:
            logging.error(f"Мониторинг ошибка: {e}")
        
        await asyncio.sleep(180)  # каждые 3 минуты

# ====================== ХЕНДЛЕРЫ ======================
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Выберите раздел:", reply_markup=get_main_keyboard())

# Зимнее содержание
@dp.message(F.text == "❄️ Зимнее содержание")
async def winter_menu(message: Message):
    await message.answer("❄️ Зимнее содержание:", reply_markup=get_winter_keyboard())

# Летнее содержание
@dp.message(F.text == "🌞 Летнее содержание")
async def summer_menu(message: Message):
    await message.answer("🌞 Летнее содержание:", reply_markup=get_summer_keyboard())

# Кнопка подрядчиков
@dp.message(F.text == "Выполнения подрядчиков 📊")
async def send_contractors(message: Message):
    today = get_msk_date_str()
    url = f"https://docs.google.com/spreadsheets/d/{CONTRACTORS_SPREADSHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(r.content, f"Выполнения подрядчиков {today}.xlsx")
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: Message):
    await message.answer("↩️ Возвращаемся в главное меню", reply_markup=get_main_keyboard())

# ====================== ЗАПУСК ======================
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    
    # Запускаем мониторинг в фоне
    asyncio.create_task(check_and_send_reports())
    
    print("Бот запущен. Автоотправка настроена в группу Эксплуатация")
    await dp.start_polling(bot, allowed_updates=["message"], drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())