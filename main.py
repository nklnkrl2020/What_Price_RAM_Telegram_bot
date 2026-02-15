import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


url = "https://www.dns-shop.ru/product/66c8c7c94231ed20/operativnaa-pamat-adata-xpg-lancer-blade-ax5u5600c4616g-dtlabbk-32-gb/"

options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = uc.Chrome(
    options=options,
    use_subprocess=True
)

try:
    driver.get("https://www.dns-shop.ru/")

    # Ждём главную
    time.sleep(random.uniform(3, 5))

    # Переходим на товар через главную (важно!)
    driver.get(url)

    time.sleep(random.uniform(5, 8))

    # Немного скроллим как человек
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(random.uniform(2, 4))

    wait = WebDriverWait(driver, 20)

    price = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".product-buy__price"))
    )

    print("Цена:", price.text)

except Exception as e:
    print("Ошибка:", e)

finally:
    time.sleep(5)
    driver.quit()
