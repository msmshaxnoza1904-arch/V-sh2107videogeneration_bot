import os
import re
import html
import uuid
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    FSInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.enums import ChatAction, ParseMode
from aiogram.client.default import DefaultBotProperties

import config
from downloader import download_instagram_video
from converter import get_available_formats, convert_file

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Instagram havolalarini aniqlash uchun regex
INSTAGRAM_REGEX = re.compile(
    r'(https?://(?:www\.)?instagram\.com/(?:reel|p|tv|share/[a-zA-Z0-9_-]+)/[a-zA-Z0-9_-]+(?:/[^\s]*)?)'
)
GENERAL_INSTA_REGEX = re.compile(
    r'(https?://(?:www\.)?instagram\.com/[^\s]+)'
)

# Kutilayotgan konvertatsiya fayllarini saqlash (xotirada)
# kalit: short_id -> {'file_id': ..., 'file_name': ...}
PENDING_FILES: dict[str, dict] = {}

dp = Dispatcher()

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


# Asosiy menyu klaviaturasi (2 ta alohida tugma)
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Instagram Video Yuklash")],
        [KeyboardButton(text="🔄 Fayl Formatini O'zgartirish")]
    ],
    resize_keyboard=True,
    is_persistent=True
)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """
    /start buyrug'i uchun xabar.
    """
    user_name = message.from_user.first_name or "Foydalanuvchi"
    text = (
        f"👋 <b>Assalomu alaykum, {user_name}!</b>\n\n"
        "Men <b>ko'p funksiyali</b> Telegram botman.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang:\n"
        "1️⃣ <b>📥 Instagram Video Yuklash</b> — Reels yoki Post videosini yuklash.\n"
        "2️⃣ <b>🔄 Fayl Formatini O'zgartirish</b> — rasm, video, audio formatini o'zgartirish."
    )
    await message.answer(text, reply_markup=main_menu, parse_mode=ParseMode.HTML)


@dp.message(F.text == "📥 Instagram Video Yuklash")
async def btn_insta_handler(message: Message):
    text = (
        "📥 <b>Instagram Video Yuklash bo'limi:</b>\n\n"
        "Marhamat, Instagram ilovasidan video yoki Reels havolasini nusxalab, shu yerga yuboring!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(F.text == "🔄 Fayl Formatini O'zgartirish")
async def btn_convert_handler(message: Message):
    text = (
        "🔄 <b>Fayl Formatini O'zgartirish bo'limi:</b>\n\n"
        "Menga o'zgartirmoqchi bo'lgan faylingizni yuboring:\n"
        "• 📄 <b>Hujjatlar:</b> PDF ➡️ Word (DOCX) yoki Excel (XLSX)\n"
        "• 📄 <b>Hujjatlar:</b> Word yoki Excel ➡️ PDF\n"
        "• 🖼 <b>Rasmlar:</b> JPG, PNG, WEBP, PDF, BMP\n"
        "• 🎬 <b>Videolar:</b> MP4, AVI, GIF yoki videodan MP3 audio ajratish\n"
        "• 🎵 <b>Audiolar / Ovoz:</b> MP3, WAV, OGG, M4A\n\n"
        "Faylni yuborganingizdan so'ng, qaysi formatga o'tkazish tugmalari chiqadi!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """
    /help buyrug'i uchun xabar.
    """
    text = (
        "📖 <b>Botdan foydalanish yo'riqnomasi:</b>\n\n"
        "🎬 <b>1. Instagram video yuklash:</b>\n"
        "• Instagram ilovasidan video yoki Reels havolasidan nusxa oling.\n"
        "• Havolani botga yuboring va video formatida qabul qiling.\n\n"
        "🔄 <b>2. Fayl formatini o'zgartirish:</b>\n"
        "• Botga istalgan faylni (PDF, Word, Excel, rasm, video yoki audio) yuboring.\n"
        "• Bot sizga mavjud formatlar tugmalarini chiqaradi.\n"
        "• Kerakli formatni tanlang va o'zgartirilgan faylni yuklab oling!\n\n"
        "📌 <b>Qo'llab-quvvatlanadigan asosiy formatlar:</b>\n"
        "• <b>PDF:</b> Word (DOCX), Excel (XLSX), Rasm (JPG), Matn (TXT)\n"
        "• <b>Word (DOCX):</b> PDF, Matn\n"
        "• <b>Excel (XLSX):</b> PDF, CSV\n"
        "• <b>Rasmlar:</b> JPG, PNG, WEBP, PDF, BMP\n"
        "• <b>Videolar:</b> MP4, MP3 (videodan audio ajratish), GIF, AVI, MKV\n"
        "• <b>Audiolar:</b> MP3, WAV, OGG, M4A, AAC, FLAC"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


# =========================================================================
# 1-FUNKSIYA: INSTAGRAM VIDEO YUKLOVCHI
# =========================================================================

@dp.message(F.text)
async def handle_instagram_link(message: Message, bot: Bot):
    """
    Foydalanuvchidan kelgan havolani tahlil qilib, videoni yuklab yuboradi.
    """
    text = message.text.strip()
    match = INSTAGRAM_REGEX.search(text) or GENERAL_INSTA_REGEX.search(text)

    if not match:
        await message.reply(
            "⚠️ <b>Noma'lum buyruq yoki havola.</b>\n\n"
            "• Video yuklash uchun Instagram havolasini yuboring.\n"
            "• Formatni o'zgartirish uchun esa fayl (rasm, video, audio) yuboring.",
            parse_mode=ParseMode.HTML
        )
        return

    url = match.group(0)
    status_msg = await message.reply("⏳ <b>Video yuklanmoqda, kuting...</b>", parse_mode=ParseMode.HTML)

    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)

    file_path = None
    try:
        video_data = await download_instagram_video(url)
        file_path = video_data['file_path']

        await status_msg.edit_text("📤 <b>Video Telegram'ga yuklanmoqda...</b>", parse_mode=ParseMode.HTML)

        video_file = FSInputFile(file_path)
        bot_user = await bot.get_me()

        caption = (
            f"🎬 <b>{html.escape(video_data['title'])}</b>\n\n"
            f"🤖 @{bot_user.username} orqali yuklandi"
        )

        await message.answer_video(
            video=video_file,
            caption=caption,
            duration=int(video_data['duration']) if video_data.get('duration') else None,
            width=video_data.get('width'),
            height=video_data.get('height'),
            supports_streaming=True,
            parse_mode=ParseMode.HTML
        )

        await status_msg.delete()

    except ValueError as ve:
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {html.escape(str(ve))}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("Kutilmagan xatolik:")
        await status_msg.edit_text(
            "❌ <b>Kechirasiz, videoni yuklab bo'lmadi.</b>\n"
            "Havola noto'g'ri yoki video mavjud bo'lmasligi mumkin.",
            parse_mode=ParseMode.HTML
        )
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


# =========================================================================
# 2-FUNKSIYA: FAYL FORMATINI O'ZGARTIRISH (KONVERTER)
# =========================================================================

async def offer_conversion(message: Message, file_id: str, file_name: str, file_size: int | None):
    """
    Faylni qabul qilib, unga mos konvertatsiya formatlari tugmalarini ko'rsatadi.
    """
    # Telegram API cheklovi: 20 MB gacha yuklab olish mumkin
    if file_size and file_size > 20 * 1024 * 1024:
        await message.reply(
            "⚠️ <b>Fayl hajmi juda katta!</b>\n"
            "Telegram botlari orqali maksimal 20 MB gacha bo'lgan fayllarni konvertatsiya qilish mumkin.",
            parse_mode=ParseMode.HTML
        )
        return

    cat, formats = get_available_formats(file_name)
    if not formats:
        await message.reply(
            "⚠️ <b>Ushbu formatni o'zgartirish qo'llab-quvvatlanmaydi.</b>\n\n"
            "Bot quyidagilarni o'zgartira oladi:\n"
            "• <b>Hujjatlar:</b> PDF ➡️ Word/Excel, Word/Excel ➡️ PDF\n"
            "• <b>Rasmlar:</b> JPG, PNG, WEBP, PDF, BMP\n"
            "• <b>Videolar:</b> MP4, AVI, MKV, MOV, GIF, MP3\n"
            "• <b>Audiolar:</b> MP3, WAV, OGG, M4A, AAC, FLAC",
            parse_mode=ParseMode.HTML
        )
        return

    # Qisqa kalit yaratish va ma'lumotni eslab qolish
    short_key = uuid.uuid4().hex[:8]
    PENDING_FILES[short_key] = {
        'file_id': file_id,
        'file_name': file_name
    }

    # Tugmalarni 2 tadan yoki 3 tadan chiroyli joylashtirish
    buttons = []
    row = []
    for fmt in formats:
        label = fmt.upper()
        if fmt == "docx":
            label = "📝 Word (DOCX)"
        elif fmt == "xlsx":
            label = "📊 Excel (XLSX)"
        elif fmt == "pdf":
            label = "📄 PDF"
        elif fmt == "mp3" and cat == "video":
            label = "🎵 MP3 (Audio)"
        elif fmt == "gif" and cat == "video":
            label = "🎞 GIF"
        elif fmt == "jpg" and cat == "document":
            label = "🖼 Rasm (JPG)"
        elif fmt == "txt":
            label = "📄 Matn (TXT)"
        elif fmt == "csv":
            label = "📑 CSV"

        row.append(InlineKeyboardButton(text=label, callback_data=f"cv:{fmt}:{short_key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.reply(
        f"📁 <b>Fayl:</b> <code>{html.escape(file_name)}</code>\n"
        f"🎯 <b>Qaysi formatga o'zgartirmoqchisiz?</b> Quyidagilardan birini tanlang:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@dp.message(F.photo)
async def handle_photo(message: Message):
    # Eng yuqori sifatli rasmni olish
    photo = message.photo[-1]
    await offer_conversion(message, photo.file_id, "image.jpg", photo.file_size)


@dp.message(F.video)
async def handle_video(message: Message):
    video = message.video
    name = video.file_name or "video.mp4"
    await offer_conversion(message, video.file_id, name, video.file_size)


@dp.message(F.audio)
async def handle_audio(message: Message):
    audio = message.audio
    name = audio.file_name or "audio.mp3"
    await offer_conversion(message, audio.file_id, name, audio.file_size)


@dp.message(F.voice)
async def handle_voice(message: Message):
    voice = message.voice
    await offer_conversion(message, voice.file_id, "voice.ogg", voice.file_size)


@dp.message(F.video_note)
async def handle_video_note(message: Message):
    video_note = message.video_note
    await offer_conversion(message, video_note.file_id, "round_video.mp4", video_note.file_size)


@dp.message(F.document)
async def handle_document(message: Message):
    doc = message.document
    name = doc.file_name or "document.bin"
    await offer_conversion(message, doc.file_id, name, doc.file_size)


@dp.callback_query(F.data.startswith("cv:"))
async def handle_conversion_callback(callback: CallbackQuery, bot: Bot):
    """
    Foydalanuvchi format tugmasini bosganda ishlaydi.
    """
    _, target_fmt, short_key = callback.data.split(":")
    file_info = PENDING_FILES.get(short_key)

    if not file_info:
        await callback.answer("⚠️ Fayl muddati tugagan. Iltimos, faylni qaytadan yuboring.", show_alert=True)
        return

    await callback.answer()
    status_msg = await callback.message.reply(
        f"⏳ <b>Fayl yuklab olinmoqda va {target_fmt.upper()} formatiga o'zgartirilmoqda...</b>",
        parse_mode=ParseMode.HTML
    )

    file_id = file_info['file_id']
    original_name = file_info['file_name']
    _, ext = os.path.splitext(original_name)
    if not ext:
        ext = ".bin"

    temp_input = os.path.join(TEMP_DIR, f"in_{short_key}{ext}")
    converted_path = None

    try:
        # Telegram'dan faylni yuklab olish
        tg_file = await bot.get_file(file_id)
        await bot.download_file(tg_file.file_path, destination=temp_input)

        # Chat action ko'rsatish
        await bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)

        # Konvertatsiya qilish
        converted_path = await convert_file(temp_input, target_fmt)

        await status_msg.edit_text("📤 <b>Tayyor! Fayl yuborilmoqda...</b>", parse_mode=ParseMode.HTML)

        out_file = FSInputFile(converted_path)
        caption = f"✅ <b>Format o'zgartirildi:</b> <code>{html.escape(os.path.basename(converted_path))}</code>"
        if target_fmt == "docx":
            caption += (
                "\n\n📝 <b>Word fayl tayyor!</b>\n"
                "💡 <i>Eslatma: Agar kompyuteringizda Word ochganda tepada sariq qatorda 'Защищенный просмотр' (Protected View) "
                "chiqsa, tahrirlash uchun 'Разрешить редактирование' (Enable Editing) tugmasini bosing.</i>"
            )

        # Formatga qarab mos turda yuborish
        if target_fmt in ("mp3", "wav", "m4a", "aac", "flac"):
            await callback.message.answer_audio(audio=out_file, caption=caption, parse_mode=ParseMode.HTML)
        elif target_fmt in ("mp4", "mov", "avi", "mkv"):
            await callback.message.answer_video(video=out_file, caption=caption, supports_streaming=True, parse_mode=ParseMode.HTML)
        elif target_fmt == "gif":
            await callback.message.answer_animation(animation=out_file, caption=caption, parse_mode=ParseMode.HTML)
        elif target_fmt in ("jpg", "png", "webp", "bmp"):
            # Rasmni hujjat sifatida yuborish sifatni saqlab qoladi
            await callback.message.answer_document(document=out_file, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await callback.message.answer_document(document=out_file, caption=caption, parse_mode=ParseMode.HTML)

        await status_msg.delete()

    except ValueError as ve:
        await status_msg.edit_text(f"❌ <b>Xatolik:</b> {html.escape(str(ve))}", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.exception("Konvertatsiyada xatolik:")
        await status_msg.edit_text(
            f"❌ <b>Konvertatsiya amalga oshmadi.</b>\nSabab: {html.escape(str(e)[:100])}",
            parse_mode=ParseMode.HTML
        )
    finally:
        # Vaqtinchalik fayllarni tozalash
        if os.path.exists(temp_input):
            try:
                os.remove(temp_input)
            except OSError:
                pass
        if converted_path and os.path.exists(converted_path):
            try:
                os.remove(converted_path)
            except OSError:
                pass


# =========================================================================
# ASOSIY ISHGA TUSHIRISH VA RENDER UCHUN HEALTH-CHECK SERVER
# =========================================================================

async def handle_health(request: web.Request) -> web.Response:
    """
    Render yoki monitoring xizmatlari (masalan, UptimeRobot) uchun 200 OK qaytaruvchi endpoint.
    """
    return web.Response(
        text="OK: Telegram Bot is active and running!",
        content_type="text/plain",
        status=200
    )


async def start_health_server():
    """
    Agar PORT muhit o'zgaruvchisi berilgan bo'lsa (Render Web Service holatida),
    avtomatik yengil aiohttp serverini ishga tushiradi.
    """
    port_str = os.getenv("PORT")
    if not port_str:
        return None

    try:
        port = int(port_str)
    except ValueError:
        port = 10000

    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health-check veb-server 0.0.0.0:{port} manzilida ishga tushdi.")
    return runner


async def main():
    if not config.BOT_TOKEN or config.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN ko'rsatilmagan! Iltimos, .env faylini to'ldiring.")
        return

    # Render Web Service uchun health-check veb serverini ishga tushirish
    runner = await start_health_server()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    finally:
        if runner:
            await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
