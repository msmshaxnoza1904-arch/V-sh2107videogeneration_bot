@echo off
title Instagram Video Downloader Bot
chcp 65001 > nul

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"

if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

cd /d "%~dp0"
echo ========================================================
echo [1/2] Kerakli kutubxonalar tekshirilmoqda va yangilanmoqda...
echo ========================================================
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo.
echo ========================================================
echo [2/2] Telegram Bot ishga tushirilmoqda...
echo ========================================================
"%PYTHON_EXE%" main.py

pause
