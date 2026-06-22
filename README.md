# 🔐 SecureVault

A Bitwarden-inspired password manager built with Python and PySide6. All vault data is encrypted at rest using PBKDF2 + AES (Fernet) — your master password never leaves your device.

---

## Features

**Vault**
- Store logins, secure notes, payment cards, and identities
- Organise items into folders with custom tags
- Favourite items for quick access
- Full-text search across all vault items
- Duplicate, edit, and delete items with confirmation prompts
- Password history — last 10 passwords saved per item

**Security**
- AES-encrypted vault file per user (480,000 PBKDF2 iterations)
- bcrypt-hashed master passwords
- Auto-lock after configurable idle time
- Clipboard auto-clear after configurable delay
- Vault health report: weak, reused, and old passwords flagged

**Password Tools**
- Password generator — length, character sets, exclude ambiguous characters
- Passphrase generator — word count, separator, capitalisation, appended number
- Username generator
- Real-time password strength analyser (score, entropy, feedback)
- TOTP secret storage

**Now Playing**
- Live media widget showing track, artist, and album
- Transport controls (previous, play/pause, next)
- Works with Spotify, Apple Music, VLC, foobar2000, YouTube Music, and more
- Cross-platform: Windows, macOS, Linux

**Settings**
- Auto-lock timer, clipboard clear timer, confirm-delete toggle
- Default sort order and list density
- Default item type and generator presets
- Accent colour themes (Indigo, Violet, Sky, Emerald, Rose, Amber)
- JSON and CSV export/import
- Folder management

---

## Installation

Download the latest installer from the [Releases](https://github.com/edgegithuber7/Secure_vault/releases/latest) page.

| Platform | File |
|----------|------|
| Windows  | `SecureVault-Setup-x.x.x.exe` |
| macOS    | `SecureVault-x.x.x.dmg` |

**macOS note:** The app is ad-hoc signed. On first launch, right-click the app → **Open**, then click **Open** in the security dialog.

Your vault data is stored locally at:
- **Windows:** `%APPDATA%\SecureVault\`
- **macOS:** `~/Library/Application Support/SecureVault/`

---

## Running from Source

**Requirements:** Python 3.12+

```bash
# Clone the repo
git clone https://github.com/edgegithuber7/Secure_vault.git
cd Secure_vault

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

---

## Building the Installers

Both installers are built automatically via GitHub Actions when a version tag is pushed (see [Releases](#releases)). To build locally:

**Windows** — requires [Inno Setup 6](https://jrsoftware.org/isinfo.php)
```bat
build.bat
```
Output: `dist\SecureVault-Setup-x.x.x.exe`

**macOS** — requires Homebrew
```bash
bash build.sh
```
Output: `dist/SecureVault-x.x.x.dmg`

---

## Releases

To publish a new release with both installers attached automatically:

```bash
# Bump version in updater.py, SecureVault.spec, installer/securevault.iss
git add -A
git commit -m "chore: bump to v1.x.x"
git push origin main

git tag v1.x.x
git push origin v1.x.x
```

GitHub Actions builds the Windows EXE and macOS DMG, then creates a public Release with both files attached. Takes ~10 minutes. Progress visible at [Actions](https://github.com/edgegithuber7/Secure_vault/actions).

---

## Security Notes

- Vault files are encrypted — without the master password they are unreadable
- `vaults/` and `users.txt` are excluded from git via `.gitignore`
- Never commit those files to a public repository
- The app checks for updates by querying the GitHub Releases API — no data is sent, only a version number is fetched

---

## Tech Stack

| Component | Library |
|-----------|---------|
| UI | PySide6 (Qt 6) |
| Encryption | `cryptography` (PBKDF2 + Fernet/AES) |
| Auth hashing | `bcrypt` |
| Packaging | PyInstaller + Inno Setup (Windows) / create-dmg (macOS) |
| CI/CD | GitHub Actions |
