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
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")


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


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text(
            "Пришли ссылку после команды:\n/add ссылка"
        )
        return

    url = context.args[0]

    await update.message.reply_text("🔍 Ищу цену, подожди...")

    # Selenium блокирующий → запускаем в отдельном потоке
    loop = asyncio.get_event_loop()
    price = await loop.run_in_executor(None, get_price, url)

    await update.message.reply_text(f"💰 Цена:\n{price}")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("add", add))

    app.run_polling()


if __name__ == "__main__":
    main()
