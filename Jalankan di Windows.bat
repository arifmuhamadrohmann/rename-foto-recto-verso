@echo off
setlocal
cd /d "%~dp0"

where pyw >nul 2>&1
if not errorlevel 1 (
    start "" pyw -3 "%~dp0rename_recto_verso.py"
    exit /b 0
)

where pythonw >nul 2>&1
if not errorlevel 1 (
    start "" pythonw "%~dp0rename_recto_verso.py"
    exit /b 0
)

echo Python 3 belum ditemukan.
echo Unduh Python dari https://www.python.org/downloads/windows/
echo Saat instalasi, aktifkan pilihan "Add Python to PATH".
echo.
pause
exit /b 1
