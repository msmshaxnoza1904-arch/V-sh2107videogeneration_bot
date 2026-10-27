#!/usr/bin/env bash
# Xatolik yuz berganda to'xtatish
set -o errexit

# Python kutubxonalarini o'rnatish
pip install --upgrade pip
pip install -r requirements.txt

# Render Native Linux muhitida ffmpeg mavjud bo'lmasa, yuklab olish
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg tizimda topilmadi. Statik FFmpeg yuklab olinmoqda..."
    mkdir -p /tmp/ffmpeg
    curl -sL https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ -C /tmp/ffmpeg --strip-components 1
    mkdir -p bin
    cp /tmp/ffmpeg/ffmpeg bin/
    cp /tmp/ffmpeg/ffprobe bin/
    chmod +x bin/ffmpeg bin/ffprobe
    echo "FFmpeg muvaffaqiyatli bin/ papkasiga joylashtirildi."
fi
