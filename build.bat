@echo off
:: build.bat – Build SecureVault Windows installer locally
:: Prerequisites: Python 3.12+, Inno Setup 6 installed at default path

echo === SecureVault Windows Build ===

:: 1. Install dev dependencies
echo [1/4] Installing dependencies...
pip install -r requirements-dev.txt

:: 2. Generate icon
echo [2/4] Generating icon...
python create_icon.py
if errorlevel 1 (echo Failed to create icon & exit /b 1)

:: 3. Build with PyInstaller
echo [3/4] Running PyInstaller...
pyinstaller --clean SecureVault.spec
if errorlevel 1 (echo PyInstaller failed & exit /b 1)

:: 4. Build installer with Inno Setup
echo [4/4] Building installer...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
%ISCC% installer\securevault.iss
if errorlevel 1 (echo Inno Setup failed & exit /b 1)

echo.
echo Build complete!  Installer: dist\SecureVault-Setup-1.0.0.exe
