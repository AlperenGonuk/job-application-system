@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Ilk kullanim icin once kurulum.bat dosyasini calistirin.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" is_basvuru_arayuzu.py
if errorlevel 1 pause
