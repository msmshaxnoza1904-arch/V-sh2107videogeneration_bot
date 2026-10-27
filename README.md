# Ko'p Funksiyali Telegram Bot (Python)

Ushbu bot quyidagi asosiy imkoniyatlarga ega:
1. **Instagram Video Yuklovchi:** Instagram Reels, Post va IGTV videolarini yuqori sifatda yuklab beradi.
2. **Hujjatlar va Fayllar Konverteri:**
   - **PDF ➡️ Word (DOCX):** Matnlar, jadvallar va rasmlarni aniq joylashtirgan holda Word ga o'tkazish.
   - **PDF ➡️ Excel (XLSX):** PDF ichidagi barcha jadvallarni Excel jadval kataklariga ajratish.
   - **Word (DOCX, DOC) ➡️ PDF:** Hujjatni sifatli PDF holatiga o'tkazish.
   - **Excel (XLSX, XLS) ➡️ PDF:** Jadvallarni PDF formatiga o'tkazish.
   - **Rasmlar (JPG, PNG, WEBP, BMP):** JPG, PNG, WEBP va PDF formatlariga o'zgartirish.
   - **Videolar (MP4, AVI, MKV, MOV):** MP4, GIF yoki videodan MP3 audio ajratib olish.
   - **Audiolar (MP3, WAV, OGG, M4A, AAC, FLAC):** Audio formatlarni almashtirish.

---

## 🛠 Ishlatilgan texnologiyalar
- **Aiogram 3** — zamonaviy asinxron Telegram bot freymvorki.
- **yt-dlp** — Instagram video va Reels yuklovchi.
- **pdf2docx** — PDF dan Word (DOCX) ga yuqori sifatli o'girish.
- **pdfplumber & openpyxl** — PDF dan jadvallarni Excel (XLSX) ga ajratish.
- **LibreOffice (Headless)** — Word va Excel hujjatlarini 100% sifat bilan PDF ga aylantirish.
- **Pillow** — Rasmlar va PDF yaratish.
- **FFmpeg** — Video va Audio konvertatsiyasi.

---

## 🚀 Ishga tushirish

### Lokal muhitda (Windows):
[`run.bat`](file:///c:/BOT/run.bat) faylini bosing yoki terminalda:
```bash
cd c:\BOT
python main.py
```

### ☁️ Render.com da ishga tushirish (Bepul & Avtomatlashtirilgan):
1. [Render.com](https://render.com) ga kiring va GitHub akkauntingiz orqali kiring.
2. **New +** tugmasini bosib, **Web Service** tanlang.
3. GitHub repozitoriyangizni (`V-sh2107videogeneration_bot`) ulang.
4. **Environment:** `Docker` (tavsiya etiladi, FFmpeg va LibreOffice avtomatik o'rnatiladi).
5. **Environment Variables** bo'limida quyidagilarni kiriting:
   - `BOT_TOKEN`: Telegram bot tokeningiz.
6. **Create Web Service** tugmasini bosing!
7. Bot o'chib qolmasligi uchun [UptimeRobot](https://uptimerobot.com) da bepul monitor yaratib, Render bergan linkni (`https://<bot-nomi>.onrender.com/health`) har 10-15 daqiqada tekshirib turishga qo'yishingiz mumkin.
