import os
import uuid
import asyncio
import logging
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Telegram botlar uchun fayl yuklash cheklovi (50 MB)
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def _download_sync(url: str) -> dict:
    """
    yt-dlp orqali Instagram videosini yuklab oladi.
    Sinxron ishlaydi, shuning uchun asyncio.to_thread orqali chaqiriladi.
    """
    file_id = str(uuid.uuid4())[:8]
    outtmpl = os.path.join(DOWNLOAD_DIR, f"insta_{file_id}_%(id)s.%(ext)s")

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
        },
    }

    # Agar cookies.txt fayli bo'lsa (yopiq profillar yoki Instagram cheklovlarini aylanib o'tish uchun)
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except DownloadError as e:
            error_message = str(e)
            logger.error(f"Yuklashda xatolik: {error_message}")
            if "Private video" in error_message or "login" in error_message.lower():
                raise ValueError("Bu profil yopiq (private) yoki Instagram tizimga kirishni talab qilmoqda.")
            raise ValueError("Videoni yuklab bo'lmadi. Havola to'g'riligini tekshiring.")

        if not info:
            raise ValueError("Video ma'lumotlarini olib bo'lmadi.")

        # Agar karusel (bir nechta media) bo'lsa, birinchisini olamiz
        entry = info.get('entries', [info])[0] if 'entries' in info else info

        file_path = ydl.prepare_filename(entry)

        # Ba'zida yt-dlp formatni mp4 ga o'giradi, shuning uchun .mp4 tekshiramiz
        base_path, _ = os.path.splitext(file_path)
        if os.path.exists(f"{base_path}.mp4"):
            file_path = f"{base_path}.mp4"

        if not os.path.exists(file_path):
            # Katalogdagi eng yangi faylni qidirish (zaxira varianti)
            candidates = [
                os.path.join(DOWNLOAD_DIR, f)
                for f in os.listdir(DOWNLOAD_DIR)
                if f.startswith(f"insta_{file_id}")
            ]
            if candidates:
                file_path = max(candidates, key=os.path.getctime)
            else:
                raise FileNotFoundError("Yuklangan video fayli topilmadi.")

        # Fayl hajmini tekshirish
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE_BYTES:
            # Hajm katta bo'lsa, faylni o'chirib xabar beramiz
            try:
                os.remove(file_path)
            except OSError:
                pass
            raise ValueError("Video hajmi 50 MB dan katta. Telegram bot cheklovi sabab yuborib bo'lmaydi.")

        title = entry.get('title') or entry.get('description') or "Instagram Video"
        # Sarlavhani Telegram caption chekloviga moslash (qisqartirish)
        if title and len(title) > 200:
            title = title[:197] + "..."

        return {
            'file_path': file_path,
            'title': title,
            'duration': entry.get('duration'),
            'width': entry.get('width'),
            'height': entry.get('height')
        }


async def download_instagram_video(url: str) -> dict:
    """
    Instagram videosini yuklashning asinxron funksiyasi.
    """
    return await asyncio.to_thread(_download_sync, url)
