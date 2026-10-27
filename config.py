import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = os.getenv("PORT")

# Agar Render yoki serverda INSTAGRAM_COOKIES o'zgaruvchisi berilgan bo'lsa,
# cookies.txt faylini avtomatik yaratish
INSTAGRAM_COOKIES = os.getenv("INSTAGRAM_COOKIES")
if INSTAGRAM_COOKIES and not os.path.exists("cookies.txt"):
    try:
        with open("cookies.txt", "w", encoding="utf-8") as f:
            f.write(INSTAGRAM_COOKIES.strip())
    except Exception as e:
        print(f"Ogohlantirish: cookies.txt faylini yaratishda xatolik: {e}")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
    print("XATO: .env faylida BOT_TOKEN ko'rsatilmagan!")
    print("Iltimos, @BotFather orqali bot oching va tokenni kiriting.")

