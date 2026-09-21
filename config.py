import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GUARANTOR_ID = int(os.getenv("GUARANTOR_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")
WEBAPP_URL = os.getenv("WEBAPP_URL")

START_GIF = "CgACAgIAAxkBAAMDaq1XSvbOcKSe065WrMwmRin2Ml8AAmCnAALXnxBJeAER3jg671E9BA"

# Путь к фото для профита (лежит в корне проекта рядом с bot.py)
PROFIT_PHOTO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "photo_2026-09-21_22-12-17.jpg"
)
