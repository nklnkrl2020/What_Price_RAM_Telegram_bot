Telegram Price Bot

Бот для Telegram, который получает цену товара с DNS-shop через Selenium.

## Функции

- Команда `/add <ссылка>` — получает цену товара.
- Меню с кнопками "Добавить товар" и "Помощь".
- Работает с Selenium и undetected_chromedriver.

## Установка

1. Клонируем репозиторий:
git clone https://github.com/<your-username>/<repo>.git

2. Создаём виртуальное окружение:
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

3. Устанавливаем зависимости:
pip install -r requirements.txt
Создаём .env в корне проекта с токеном:

4. env
TELEGRAM_TOKEN=ВАШ_ТОКЕН

5. Запуск
python main.py