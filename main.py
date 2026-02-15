import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from playwright.async_api import async_playwright
from playwright_stealth import Stealth



import os
import asyncio
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import re

load_dotenv()

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def get_price(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml",
            "Referer": "https://www.dns-shop.ru/",
        }

        async with httpx.AsyncClient(headers=headers, timeout=20) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return f"Ошибка HTTP: {response.status_code}"

        html = response.text

        # Ищем цену через regex
        match = re.search(r'"price":\s?(\d+)', html)

        if match:
            price = match.group(1)
            return f"{price} ₽"
        else:
            return "Цена не найдена"

    except Exception as e:
        return f"Ошибка: {e}"


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет 👋\n/add ССЫЛКА")


@dp.message(Command("add"))
async def add_product(message: types.Message):
    parts = message.text.split()

    if len(parts) < 2:
        await message.answer("❌ Вставь ссылку после /add")
        return

    url = parts[1]

    await message.answer("🔎 Проверяю цену...")

    price = await get_price(url)

    await message.answer(f"💰 Цена:\n{price}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
