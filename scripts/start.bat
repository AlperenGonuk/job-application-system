@echo off
REM Uygulamayi konsol penceresi acmadan baslatir. Hata ciktisi data\app.log
REM dosyasina yazilir; sorun yasarsaniz once oraya bakin.
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\pythonw.exe" (
  echo Ilk kullanim icin once scripts\setup.bat dosyasini calistirin.
  pause
  exit /b 1
)

if not exist "data" mkdir "data"
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0
