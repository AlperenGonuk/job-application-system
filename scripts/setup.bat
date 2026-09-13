@echo off
setlocal
cd /d "%~dp0.."

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher bulunamadi. Python 3.11 veya daha yeni bir surum kurun.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Kurulum tamamlandi. Simdi scripts\start.bat dosyasini calistirabilirsiniz.
pause
exit /b 0

:error
echo.
echo Kurulum tamamlanamadi. Internet baglantisini ve Python kurulumunu kontrol edin.
pause
exit /b 1
