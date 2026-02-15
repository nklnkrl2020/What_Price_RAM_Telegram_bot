import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
import json
import re

# ======================
# НАСТРОЙКИ
# ======================

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler()

DATA_FILE = "products.json"

# ======================
# РАБОТА С ФАЙЛОМ
# ======================

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ======================
# ПАРСИНГ ЦЕНЫ
# ======================

def get_price(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Ищем цену (может потребоваться корректировка)
    price_tag = soup.find("span", {"class": "product-buy__price"})
    if not price_tag:
        return None

    price_text = price_tag.text.strip()
    price_number = re.sub(r"[^\d]", "", price_text)

    return int(price_number)

# ======================
# ДОБАВЛЕНИЕ ТОВАРА
# ======================

@dp.message(Command("add"))
async def add_product(message: Message):
    args = message.text.split()

    if len(args) < 2:
        await message.answer("Использование: /add ссылка")
        return

    url = args[1]

    price = get_price(url)

    if price is None:
        await message.answer("Не удалось получить цену. Проверь ссылку.")
        return

    data = load_data()

    user_id = str(message.from_user.id)

    if user_id not in data:
        data[user_id] = []

    data[user_id].append({
        "url": url,
        "last_price": price,
        "min_price": price,
        "max_price": price
    })

    save_data(data)

    await message.answer(f"Товар добавлен! Текущая цена: {price} ₽")

# ======================
# ПРОВЕРКА ЦЕН
# ======================

async def check_prices():
    data = load_data()

    for user_id, products in data.items():
        for product in products:
            url = product["url"]
            old_price = product["last_price"]

            new_price = get_price(url)

            if new_price is None:
                continue

            diff = new_price - old_price

            if diff == 0:
                text = f"Цена не изменилась: {new_price} ₽"
            elif diff > 0:
                text = f"Цена выросла на {diff} ₽\nСейчас: {new_price} ₽"
            else:
                text = f"Цена снизилась на {abs(diff)} ₽\nСейчас: {new_price} ₽"

            # обновляем мин/макс
            product["min_price"] = min(product["min_price"], new_price)
            product["max_price"] = max(product["max_price"], new_price)
            product["last_price"] = new_price

            save_data(data)

            text += (
                f"\n\nМинимальная цена: {product['min_price']} ₽"
                f"\nМаксимальная цена: {product['max_price']} ₽"
            )

            await bot.send_message(user_id, text)

# ======================
# СТАРТ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Отправь:\n"
        "/add ссылка\n"
        "Чтобы начать отслеживание цены."
    )

async def main():
    scheduler.add_job(check_prices, "interval", hours=24)
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
