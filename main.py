import os
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# ======================
# ЗАГРУЗКА ТОКЕНА
# ======================
load_dotenv()
TOKEN = os.getenv("TOKEN")

# ======================
# НАСТРОЙКИ БОТА
# ======================
bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
DATA_FILE = "products.json"

# ======================
# ФАЙЛ ДАННЫХ
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
# АСИНХРОННЫЙ PLAYWRIGHT
# ======================
async def get_price(url):
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(1000)

            # CSS селектор цены на DNS
            price_element = page.locator("span.product-buy__price").first
            price_text = await price_element.inner_text()
            price_number = int(''.join(filter(str.isdigit, price_text)))

            await browser.close()
            return price_number
    except Exception as e:
        print("Ошибка при парсинге:", e)
        return None

# ======================
# КОМАНДА /START
# ======================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Отправь:\n"
        "/add ссылка\n"
        "Чтобы начать отслеживать цену."
    )

# ======================
# КОМАНДА /ADD
# ======================
@dp.message(Command("add"))
async def add_product(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /add ссылка")
        return

    url = args[1]
    price = await get_price(url)
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
# ФУНКЦИЯ ПРОВЕРКИ ЦЕН
# ======================
async def check_prices():
    data = load_data()
    for user_id, products in data.items():
        for product in products:
            url = product["url"]
            old_price = product["last_price"]
            new_price = await get_price(url)
            if new_price is None:
                continue

            diff = new_price - old_price
            if diff == 0:
                text = f"Цена не изменилась: {new_price} ₽"
            elif diff > 0:
                text = f"Цена выросла на {diff} ₽\nСейчас: {new_price} ₽"
            else:
                text = f"Цена снизилась на {abs(diff)} ₽\nСейчас: {new_price} ₽"

            product["last_price"] = new_price
            product["min_price"] = min(product["min_price"], new_price)
            product["max_price"] = max(product["max_price"], new_price)
            save_data(data)

            text += (
                f"\n\nМинимальная цена: {product['min_price']} ₽"
                f"\nМаксимальная цена: {product['max_price']} ₽"
            )

            await bot.send_message(user_id, text)

# ======================
# СТАРТ ПЛАНИРОВЩИКА И БОТА
# ======================
async def main():
    scheduler.add_job(check_prices, "interval", hours=24)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
