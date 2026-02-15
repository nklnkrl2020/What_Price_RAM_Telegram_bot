import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
import json
import re
import time

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

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
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ======================
# ФУНКЦИЯ ПОЛУЧЕНИЯ ЦЕНЫ ЧЕРЕЗ SELENIUM
# ======================

def get_price(url):
    options = Options()
    options.add_argument("--headless")  # без окна
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")

    # Укажи путь к chromedriver, если он не в PATH
    service = Service(executable_path="chromedriver-win64/chromedriver-win64/chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        #time.sleep(3) # Ждём 3 секунды загрузки Json
        # Ждём до 10 секунд, пока элемент с ценой появится
        wait = WebDriverWait(driver, 10)

        # Находим цену по актуальному классу
        price_elem = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "product-card-price__current")
        ))
        #price_elem = driver.find_element(By.CLASS_NAME, "product-card-price__current")
        price_text = price_elem.text.strip()
        price_number = re.sub(r"[^\d]", "", price_text)
        return int(price_number)
    except Exception as e:
        print("Ошибка Selenium:", e)
        return None
    finally:
        driver.quit()

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
    print("Полученная цена:", price)  # для отладки

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
