import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("XATO: .env faylida BOT_TOKEN ko'rsatilmagan!")
    print("Iltimos, @BotFather orqali bot oching va tokenni .env fayliga kiriting.")
