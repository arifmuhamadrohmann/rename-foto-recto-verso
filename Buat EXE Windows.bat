@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>&1
    if errorlevel 1 goto :python_missing
    set "PYTHON_CMD=python"
)

echo [1/4] Menyiapkan lingkungan build...
if not exist ".venv-build\Scripts\python.exe" (
    %PYTHON_CMD% -m venv ".venv-build"
    if errorlevel 1 goto :build_failed
)

echo [2/4] Memasang PyInstaller...
".venv-build\Scripts\python.exe" -m pip install --upgrade pip pyinstaller
if errorlevel 1 goto :build_failed

echo [3/4] Memeriksa program...
".venv-build\Scripts\python.exe" -m py_compile "rename_recto_verso.py"
if errorlevel 1 goto :build_failed

echo [4/4] Membuat EXE portabel...
".venv-build\Scripts\python.exe" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --version-file "windows_version_info.txt" ^
    --name "RenameFotoRectoVerso" ^
    "rename_recto_verso.py"
if errorlevel 1 goto :build_failed

echo.
echo BERHASIL.
echo File portabel tersedia di:
echo %~dp0dist\RenameFotoRectoVerso.exe
echo Membuka lokasi hasil di Windows Explorer...
explorer.exe /select,"%~dp0dist\RenameFotoRectoVerso.exe"
if not defined BUILD_NO_PAUSE pause
exit /b 0

:python_missing
echo.
echo Python 3 belum ditemukan.
echo Unduh dari https://www.python.org/downloads/windows/
echo Saat instalasi, aktifkan pilihan "Add Python to PATH".
if not defined BUILD_NO_PAUSE pause
exit /b 1

:build_failed
echo.
echo Build gagal. Periksa pesan error di atas dan koneksi internet Anda.
if not defined BUILD_NO_PAUSE pause
exit /b 1
