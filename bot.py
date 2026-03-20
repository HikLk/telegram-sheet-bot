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

# ID основной таблицы (зимняя)
MAIN_SPREADSHEET_ID = "1f248h28pbE16o9pKgvJuSbh2ViKAsfTE_OK3qIRP6TA"
SINGLE_SHEET_GID = "1841691264"

# Планы от РУАД
PLANS_SPREADSHEET_ID = "1SPmkft_ZvZr4tmCBcmzN0AE7HPscy3aRwB82uqR34CU"

# Выполнения подрядчиков
CONTRACTORS_SPREADSHEET_ID = "1u7Hn4snGNAMNjMyXo7fcOUxS7vdzTS6Dj9n3J_IXVu0"

BUTTON_CONTRACTORS = "Выполнения подрядчиков 📊"

# ── НОВАЯ ЛЕТНЯЯ ТАБЛИЦА ─────────────────────────────────────
SUMMER_SPREADSHEET_ID = "14w0tzn5xsX2ZX5zgHYfEsMZ8p0ZX2f3rLhO_yR0I-3A"
DAILY_GID = "1539583525"      # данные за последние сутки
CUM_GID   = "1514416922"      # накопительные данные

# Кнопки
BUTTON_FULL_REPORT   = "Отчет по зимним видам работ ❄️"

# Фотка Андрея
BUTTON_ANDREY = "Посмотреть на Андрея 😏"   # ← можно поменять эмодзи или текст

# Летние виды работ
BUTTON_SUMMER_REPORT = "Отчет по летним видам работ 🌞"
BUTTON_DAILY_SUMMER  = "Выгрузить данные за сутки 📅"
BUTTON_CUM_SUMMER    = "Выгрузить накопительные данные 📊"
BUTTON_FULL_SUMMER   = "Выгрузить полный отчет 📋"
BUTTON_BACK          = "Назад в главное меню 🔙"

BUTTON_WORKERS_EXCEL = "Количество дорожных рабочих для МТДИ 🧑‍🏭"
BUTTON_PLANS_EXCEL   = "Планы от РУАД 📋"

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


def get_msk_date_str():
    """Возвращает сегодняшнюю дату по Москве в формате ДД.ММ.ГГГГ"""
    utc_now = datetime.now(timezone.utc)
    msk_now = utc_now + MSK_OFFSET
    return msk_now.strftime("%d.%m.%Y")


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_FULL_REPORT)],
            [KeyboardButton(text=BUTTON_WORKERS_EXCEL)],
            [KeyboardButton(text=BUTTON_PLANS_EXCEL)],
            [KeyboardButton(text=BUTTON_SUMMER_REPORT)],
            [KeyboardButton(text=BUTTON_CONTRACTORS)],
            [KeyboardButton(text=BUTTON_ANDREY)],               # ← новая кнопка
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_summer_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BUTTON_DAILY_SUMMER)],
            [KeyboardButton(text=BUTTON_CUM_SUMMER)],
            [KeyboardButton(text=BUTTON_FULL_SUMMER)],
            [KeyboardButton(text=BUTTON_BACK)],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


# ────────────────────────────────────────────────
@dp.message(CommandStart())
async def start(message: Message):
    kb = get_main_keyboard()
    await message.answer(
    "Выберите нужный отчёт:\n\n"
    "❄️ — полный отчёт зимний ...\n"
    "🧑‍🏭 — только лист с данными ...\n"
    "📋 — планы от РУАД ...\n"
    "🌞 — отчет по летним видам ...\n"
    "📊 — выполнения подрядчиков ...\n"
    "😏 — посмотреть на Андрея",
    reply_markup=kb
)


# ── Полный отчёт зимний (оставлен без изменений) ─────────────────────
@dp.message(F.text == BUTTON_FULL_REPORT)
async def send_full_report(message: Message):
    base_name, report_text = get_report_info()
    excel_filename = f"{base_name}.xlsx"
    pdf_filename = f"{base_name}.pdf"
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


# ── Только лист рабочих (оставлен без изменений) ─────────────────────
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


# ── Планы от РУАД (оставлен без изменений) ───────────────────────────
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

# ── Выполнения подрядчиков (оставлен без изменений) ───────────────────────────
@dp.message(F.text == BUTTON_CONTRACTORS)
async def send_contractors_excel(message: Message):
    today = get_msk_date_str()
    filename = f"Выполнения подрядчиков {today}.xlsx"
    
    url = f"https://docs.google.com/spreadsheets/d/{CONTRACTORS_SPREADSHEET_ID}/export?format=xlsx"
    
    await message.answer(f"📊 Выгружаю выполнения подрядчиков на {today}...")
    
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=filename),
            caption="Полная таблица выполнений подрядчиков в Excel"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить таблицу подрядчиков: {str(e)}")

# ── Фото Андрея (оставлен без изменений) ───────────────────────────
@dp.message(F.text == BUTTON_ANDREY)
async def send_andrey_photo(message: Message):
    photo_url = "https://i.ibb.co/XZ8GpFxV/photo-2025-09-19-15-29-08.jpg"  # прямая ссылка на изображение
    
    try:
        # Отправляем фото с подписью (можно убрать или изменить caption)
        await message.answer_photo(
            photo=photo_url,
            caption="Вот Андрей 👀"
        )
    except Exception as e:
        await message.answer(f"Не удалось отправить фото 😔\nОшибка: {str(e)}")


# ── МЕНЮ ЛЕТНИХ ВИДОВ РАБОТ ──────────────────────────────────────────
@dp.message(F.text == BUTTON_SUMMER_REPORT)
async def summer_menu(message: Message):
    await message.answer(
        "Выберите тип отчёта по летним видам работ:",
        reply_markup=get_summer_keyboard()
    )


@dp.message(F.text == BUTTON_DAILY_SUMMER)
async def send_daily_summer(message: Message):
    today = get_msk_date_str()
    base_name = f"Данные за сутки {today}"
    excel_filename = f"{base_name}.xlsx"
    pdf_filename = f"{base_name}.pdf"

    await message.answer(f"📅 Выгружаю данные за сутки ({today})...")

    gid = DAILY_GID
    # Excel
    url = f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx&gid={gid}"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=excel_filename),
            caption=None
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить Excel (сутки): {str(e)}")
        return

    # PDF
    pdf_url = (
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={gid}&size=A3&portrait=false&fitw=true&"
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
        await message.answer(f"❌ Не удалось выгрузить PDF (сутки): {str(e)}")


@dp.message(F.text == BUTTON_CUM_SUMMER)
async def send_cum_summer(message: Message):
    today = get_msk_date_str()
    base_name = f"Накопительные данные {today}"
    excel_filename = f"{base_name}.xlsx"
    pdf_filename = f"{base_name}.pdf"

    await message.answer(f"📊 Выгружаю накопительные данные ({today})...")

    gid = CUM_GID
    # Excel
    url = f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx&gid={gid}"
    try:
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=excel_filename),
            caption=None
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить Excel (накопительные): {str(e)}")
        return

    # PDF
    pdf_url = (
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={gid}&size=A3&portrait=false&fitw=true&"
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
        await message.answer(f"❌ Не удалось выгрузить PDF (накопительные): {str(e)}")


@dp.message(F.text == BUTTON_FULL_SUMMER)
async def send_full_summer(message: Message):
    today = get_msk_date_str()
    base_name = f"Отчет по летнему содержанию {today}"
    excel_filename = f"{base_name}.xlsx"
    
    await message.answer(f"📋 Выгружаю полный отчет по летнему содержанию ({today})...")

    # 1. Excel — вся таблица
    url_excel = f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?format=xlsx"
    try:
        r = requests.get(url_excel, timeout=40)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=excel_filename),
            caption="Полная таблица (все листы) в Excel"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить Excel (полный): {str(e)}")
        return

    # 2. PDF — данные за сутки
    pdf_filename_daily = f"{base_name} — сутки.pdf"
    pdf_url_daily = (
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={DAILY_GID}&size=A3&portrait=false&fitw=true&"
        f"gridlines=false&printtitle=false&sheetnames=false&fzr=false"
    )
    try:
        r = requests.get(pdf_url_daily, timeout=30)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=pdf_filename_daily),
            caption="Лист с данными за сутки"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить PDF (сутки): {str(e)}")

    # 3. PDF — накопительные данные
    pdf_filename_cum = f"{base_name} — накопительные.pdf"
    pdf_url_cum = (
        f"https://docs.google.com/spreadsheets/d/{SUMMER_SPREADSHEET_ID}/export?"
        f"format=pdf&gid={CUM_GID}&size=A3&portrait=false&fitw=true&"
        f"gridlines=false&printtitle=false&sheetnames=false&fzr=false"
    )
    try:
        r = requests.get(pdf_url_cum, timeout=30)
        r.raise_for_status()
        await message.answer_document(
            document=BufferedInputFile(file=r.content, filename=pdf_filename_cum),
            caption="Лист с накопительными данными"
        )
    except Exception as e:
        await message.answer(f"❌ Не удалось выгрузить PDF (накопительные): {str(e)}")


@dp.message(F.text == BUTTON_BACK)
async def back_to_main(message: Message):
    await message.answer(
        "Возвращаемся в главное меню",
        reply_markup=get_main_keyboard()
    )


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