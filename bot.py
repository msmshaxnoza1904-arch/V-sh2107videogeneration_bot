"""
Render yoki boshqa muhitlarda 'python bot.py' deb ishga tushirilganda
asosiy 'main.py' faylini chaqiruvchi modul.
"""
import asyncio
from main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
