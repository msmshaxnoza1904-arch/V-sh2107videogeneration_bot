FROM python:3.12-slim

# Tizim paketlari (ffmpeg, libreoffice va shriftlar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libreoffice-nogui \
    fonts-dejavu \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kutubxonalarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Loyihaning barcha fayllarini nusxalash
COPY . .

# Render porti
ENV PORT=10000

# Botni ishga tushirish
CMD ["python", "main.py"]
