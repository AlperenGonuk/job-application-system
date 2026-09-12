@echo off
REM Sorun giderme icin: uygulamayi konsol penceresiyle birlikte baslatir,
REM boylece hata mesajlari ekranda gorunur.
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Ilk kullanim icin once scripts\setup.bat dosyasini calistirin.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
