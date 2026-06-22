#!/usr/bin/env bash
# build.sh – Build SecureVault macOS DMG locally
# Prerequisites: Python 3.12+, Homebrew, create-dmg
# Usage: bash build.sh

set -euo pipefail
echo "=== SecureVault macOS Build ==="

# 1. Dependencies
echo "[1/5] Installing Python dependencies..."
pip install -r requirements-dev.txt

# 2. Icon PNGs
echo "[2/5] Generating icon PNGs..."
python create_icon.py

# 3. Build ICNS from PNGs
echo "[3/5] Building icon.icns..."
ICONSET="assets/icon.iconset"
mkdir -p "$ICONSET"
cp assets/icon_16.png  "$ICONSET/icon_16x16.png"
cp assets/icon_32.png  "$ICONSET/icon_16x16@2x.png"
cp assets/icon_32.png  "$ICONSET/icon_32x32.png"
cp assets/icon_64.png  "$ICONSET/icon_32x32@2x.png"
cp assets/icon_128.png "$ICONSET/icon_128x128.png"
cp assets/icon_256.png "$ICONSET/icon_128x128@2x.png"
cp assets/icon_256.png "$ICONSET/icon_256x256.png"
cp assets/icon_512.png "$ICONSET/icon_256x256@2x.png"
cp assets/icon_512.png "$ICONSET/icon_512x512.png"
iconutil -c icns "$ICONSET" -o assets/icon.icns
echo "  assets/icon.icns"

# 4. PyInstaller
echo "[4/5] Running PyInstaller..."
pyinstaller --clean SecureVault.spec

# 5. Create DMG
echo "[5/5] Building DMG..."
if ! command -v create-dmg &>/dev/null; then
    echo "  Installing create-dmg via Homebrew..."
    brew install create-dmg
fi

APP="dist/SecureVault.app"
DMG="dist/SecureVault-1.0.0.dmg"

create-dmg \
    --volname "SecureVault" \
    --volicon "assets/icon.icns" \
    --window-pos 200 120 \
    --window-size 580 380 \
    --icon-size 120 \
    --icon "SecureVault.app" 145 185 \
    --hide-extension "SecureVault.app" \
    --app-drop-link 435 185 \
    "$DMG" \
    "$APP"

echo ""
echo "Build complete!  DMG: $DMG"
