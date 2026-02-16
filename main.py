import time
import random
import asyncio
import os
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import MessageHandler, filters

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")


import json

DATA_FILE = "products.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("➕ Добавить товар")],
        [KeyboardButton("📦 Мои товары")],
        [KeyboardButton("❌ Удалить товар")]
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )


def get_price(url):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = uc.Chrome(options=options, use_subprocess=True)

    try:
        driver.get("https://www.dns-shop.ru/")
        time.sleep(random.uniform(3, 5))

        driver.get(url)
        time.sleep(random.uniform(5, 8))

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight/2);"
        )
        time.sleep(random.uniform(2, 4))

        wait = WebDriverWait(driver, 20)

        price_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".product-buy__price")
            )
        )

        return price_element.text

    except Exception as e:
        return f"Ошибка: {e}"

    finally:
        try:
            driver.quit()
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать 👋\nВыбери действие:",
        reply_markup=main_menu_keyboard()
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Пришли ссылку после команды:\n/add ссылка"
        )
        return

    url = context.args[0]
    user_id = str(update.effective_user.id)

    await update.message.reply_text("🔍 Ищу цену, подожди...")

    loop = asyncio.get_event_loop()
    price_text = await loop.run_in_executor(None, get_price, url)

    if "Ошибка" in price_text:
        await update.message.reply_text(price_text)
        return

    # оставляем только цифры
    price = int("".join(filter(str.isdigit, price_text)))

    data = load_data()

    if user_id not in data:
        data[user_id] = []

    data[user_id].append({
        "url": url,
        "last_price": price,
        "min_price": price,
        "max_price": price
    })

    save_data(data)

    await update.message.reply_text(
        f"✅ Товар добавлен\nТекущая цена: {price} ₽"
    )

async def check_prices(app):

    data = load_data()

    for user_id, products in data.items():
        for product in products:

            url = product["url"]
            old_price = product["last_price"]

            loop = asyncio.get_event_loop()
            price_text = await loop.run_in_executor(None, get_price, url)

            if "Ошибка" in price_text:
                continue

            new_price = int("".join(filter(str.isdigit, price_text)))

            diff = new_price - old_price

            if diff == 0:
                message = f"Цена не изменилась: {new_price} ₽"
            elif diff > 0:
                message = (
                    f"📈 Цена выросла на {diff} ₽\n"
                    f"Сейчас: {new_price} ₽"
                )
            else:
                message = (
                    f"📉 Цена снизилась на {abs(diff)} ₽\n"
                    f"Сейчас: {new_price} ₽"
                )

            product["min_price"] = min(product["min_price"], new_price)
            product["max_price"] = max(product["max_price"], new_price)
            product["last_price"] = new_price

            message += (
                f"\n\nМинимальная цена: {product['min_price']} ₽"
                f"\nМаксимальная цена: {product['max_price']} ₽"
            )

            await app.bot.send_message(chat_id=user_id, text=message)

    save_data(data)

async def list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]:
        await update.message.reply_text("У тебя нет отслеживаемых товаров.")
        return

    message = "📦 Твои товары:\n\n"

    for i, product in enumerate(data[user_id], start=1):
        message += (
            f"{i}. {product['url']}\n"
            f"   Текущая цена: {product['last_price']} ₽\n"
            f"   Мин: {product['min_price']} ₽ | "
            f"Макс: {product['max_price']} ₽\n\n"
        )

    await update.message.reply_text(message)

async def remove_product(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id]:
        await update.message.reply_text("У тебя нет товаров для удаления.")
        return

    if not context.args:
        await update.message.reply_text(
            "Укажи номер товара:\n/remove 1"
        )
        return

    try:
        index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("Нужно указать число.")
        return

    if index < 0 or index >= len(data[user_id]):
        await update.message.reply_text("Товара с таким номером нет.")
        return

    removed_product = data[user_id].pop(index)

    save_data(data)

    await update.message.reply_text(
        f"❌ Товар удалён:\n{removed_product['url']}"
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if context.user_data.get("waiting_for_url"):
        context.user_data["waiting_for_url"] = False
        context.args = [text]
        await add(update, context)
        return

    if text == "➕ Добавить товар":
        await update.message.reply_text(
            "Отправь ссылку на товар:"
        )
        context.user_data["waiting_for_url"] = True

    elif text == "📦 Мои товары":
        await list_products(update, context)

    elif text == "❌ Удалить товар":
        await update.message.reply_text(
            "Напиши номер товара для удаления:\n/remove 1"
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_products))
    app.add_handler(CommandHandler("remove", remove_product))

    # запуск проверки раз в 24 часа
    app.job_queue.run_repeating(
        check_prices,
        interval=86400,  # 24 часа
        #first=10         # первый запуск через 10 секунд
    )

    app.run_polling()




if __name__ == "__main__":
    main()
