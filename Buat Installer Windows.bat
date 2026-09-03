@echo off
setlocal
cd /d "%~dp0"

set "BUILD_NO_PAUSE=1"
call "Buat EXE Windows.bat"
if errorlevel 1 goto :installer_failed

set "ISCC_EXE="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if not defined ISCC_EXE if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_EXE=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

if not defined ISCC_EXE goto :inno_missing

echo.
echo Membuat installer Windows...
"%ISCC_EXE%" "installer_windows.iss"
if errorlevel 1 goto :installer_failed

echo.
echo BERHASIL.
echo Installer tersedia di folder:
echo %~dp0installer
echo Membuka lokasi hasil di Windows Explorer...
explorer.exe /select,"%~dp0installer\Setup-RenameFotoRectoVerso-1.0.3.exe"
pause
exit /b 0

:inno_missing
echo.
echo Inno Setup 6 belum ditemukan.
echo Instal Inno Setup 6 dari https://jrsoftware.org/isdl.php
echo Setelah itu, jalankan file ini kembali.
pause
exit /b 1

:installer_failed
echo.
echo Pembuatan installer gagal. Periksa pesan error di atas.
pause
exit /b 1
