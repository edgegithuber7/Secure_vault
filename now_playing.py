"""
now_playing.py – Cross-platform media session info and controls.

Windows: PowerShell process window-title scanning + ctypes virtual key codes.
macOS:   AppleScript queries to Spotify, Music, VLC, etc.
Linux:   playerctl (if installed).
"""

from __future__ import annotations

import platform
import re
import subprocess

_OS = platform.system()  # "Windows" | "Darwin" | "Linux"


# ══════════════════════════════════════════════════════════════════════
# Windows implementation
# ══════════════════════════════════════════════════════════════════════

_WIN_PLAYERS = [
    ("Spotify",              "Spotify",    r"^(?P<artist>.+?) - (?P<title>.+)$"),
    ("VLC",                  "vlc",        r"^(?P<title>.+?) - VLC media player$"),
    ("foobar2000",           "foobar2000", r"^(?P<title>.+?) - foobar2000"),
    ("MusicBee",             "MusicBee",   r"^(?P<title>.+?) - MusicBee"),
    ("Winamp",               "winamp",     r"^\d+\. (?P<title>.+?) - Winamp$"),
    ("iTunes",               "iTunes",     r"^(?P<title>.+?) - iTunes$"),
    ("Windows Media Player", "wmplayer",   r"^(?P<title>.+?) - Windows Media Player$"),
    ("Groove Music",         "Music",      r"^(?P<title>.+?) - Groove Music$"),
]

_WIN_BROWSERS   = ["chrome", "msedge", "firefox"]
_WIN_BROWSER_RE = [
    ("YouTube Music", r"^(?P<title>.+?) - YouTube Music$"),
    ("Spotify Web",   r"^(?P<artist>.+?) - (?P<title>.+?) - Spotify$"),
    ("SoundCloud",    r"^(?P<title>.+?) by (?P<artist>.+?) \| SoundCloud$"),
]

_WIN_IDLE = {
    "spotify":    {"Spotify", "Spotify Premium", "Spotify Free"},
    "music":      {"Groove Music"},
}

VK_PLAY_PAUSE = 0xB3
VK_NEXT       = 0xB0
VK_PREV       = 0xB1
KEYUP         = 0x0002


def _win_get_titles() -> dict[str, str]:
    all_names = [p[1] for p in _WIN_PLAYERS] + _WIN_BROWSERS
    ps_list   = ", ".join(f"'{n}'" for n in all_names)
    ps = f"""
$names = @({ps_list})
foreach ($name in $names) {{
    $p = Get-Process -Name $name -ErrorAction SilentlyContinue |
         Where-Object {{ $_.MainWindowTitle -ne '' }} | Select-Object -First 1
    if ($p) {{ Write-Output "$($p.Name)|$($p.MainWindowTitle)" }}
}}
"""
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps],
            capture_output=True, text=True, timeout=5,
        )
        out: dict[str, str] = {}
        for line in r.stdout.strip().splitlines():
            if "|" in line:
                k, v = line.split("|", 1)
                out[k.strip().lower()] = v.strip()
        return out
    except Exception:
        return {}


def _win_get() -> dict | None:
    titles = _win_get_titles()

    for app_name, proc, pattern in _WIN_PLAYERS:
        wt   = titles.get(proc.lower(), "")
        idle = _WIN_IDLE.get(proc.lower(), set())
        if not wt or wt in idle:
            continue
        m = re.match(pattern, wt, re.IGNORECASE)
        if m:
            g = m.groupdict()
            return {"title": g.get("title", wt).strip(), "artist": g.get("artist", "").strip(),
                    "album": "", "app": app_name, "status": "Playing"}
        return {"title": wt, "artist": "", "album": "", "app": app_name, "status": "Playing"}

    for browser in _WIN_BROWSERS:
        wt = titles.get(browser, "")
        if not wt:
            continue
        for svc, pattern in _WIN_BROWSER_RE:
            m = re.match(pattern, wt, re.IGNORECASE)
            if m:
                g = m.groupdict()
                return {"title": g.get("title", "").strip(), "artist": g.get("artist", "").strip(),
                        "album": "", "app": svc, "status": "Playing"}
    return None


def _win_control(action: str) -> bool:
    vk_map = {"play_pause": VK_PLAY_PAUSE, "next": VK_NEXT, "prev": VK_PREV}
    vk = vk_map.get(action)
    if not vk:
        return False
    try:
        import ctypes
        u = ctypes.windll.user32
        u.keybd_event(vk, 0, 0, 0)
        u.keybd_event(vk, 0, KEYUP, 0)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
# macOS implementation
# ══════════════════════════════════════════════════════════════════════

# AppleScript for each app; returns "title|artist|album|status" or empty string
_MAC_SCRIPTS: list[tuple[str, str]] = [
    ("Spotify", """
        tell application "System Events"
            if exists process "Spotify" then
                tell application "Spotify"
                    set s to player state as string
                    if s is "playing" or s is "paused" then
                        set t to name of current track
                        set a to artist of current track
                        set al to album of current track
                        return t & "|" & a & "|" & al & "|" & s
                    end if
                end tell
            end if
        end tell
    """),
    ("Music", """
        tell application "System Events"
            if exists process "Music" then
                tell application "Music"
                    set s to player state as string
                    if s is "playing" or s is "paused" then
                        set t to name of current track
                        set a to artist of current track
                        set al to album of current track
                        return t & "|" & a & "|" & al & "|" & s
                    end if
                end tell
            end if
        end tell
    """),
    ("VLC", """
        tell application "System Events"
            if exists process "VLC" then
                tell application "VLC"
                    set t to name of current item
                    return t & "|||playing"
                end tell
            end if
        end tell
    """),
    ("Tidal", """
        tell application "System Events"
            if exists process "TIDAL" then
                set w to name of first window of process "TIDAL"
                return w & "|||playing"
            end if
        end tell
    """),
]

_MAC_CTRL: dict[str, dict[str, str]] = {
    "Spotify": {
        "play_pause": "playpause",
        "next":       "next track",
        "prev":       "previous track",
    },
    "Music": {
        "play_pause": "playpause",
        "next":       "next track",
        "prev":       "previous track",
    },
}


def _osascript(script: str) -> str:
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=4,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def _mac_get() -> dict | None:
    for app_name, script in _MAC_SCRIPTS:
        out = _osascript(script)
        if not out:
            continue
        parts = out.split("|")
        title  = parts[0].strip() if parts else ""
        artist = parts[1].strip() if len(parts) > 1 else ""
        album  = parts[2].strip() if len(parts) > 2 else ""
        status = parts[3].strip().title() if len(parts) > 3 else "Playing"
        if title:
            return {"title": title, "artist": artist, "album": album,
                    "app": app_name, "status": status}
    return None


def _mac_control(action: str) -> bool:
    # Try app-specific AppleScript first (Spotify, Music)
    for app, cmds in _MAC_CTRL.items():
        cmd = cmds.get(action)
        if not cmd:
            continue
        script = (
            f'tell application "System Events" to '
            f'if exists process "{app}" then '
            f'tell application "{app}" to {cmd}'
        )
        out = _osascript(script)
        if out is not None:
            return True
    # Fallback: simulate media key via key code (requires Accessibility permission)
    key_map = {"play_pause": "179", "next": "176", "prev": "177"}
    code = key_map.get(action)
    if code:
        script = (
            f'tell application "System Events" to '
            f'key code {code}'
        )
        _osascript(script)
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
# Linux implementation (playerctl)
# ══════════════════════════════════════════════════════════════════════

def _linux_get() -> dict | None:
    try:
        r = subprocess.run(
            ["playerctl", "metadata", "--format",
             "{{title}}|{{artist}}|{{album}}|{{status}}"],
            capture_output=True, text=True, timeout=3,
        )
        out = r.stdout.strip()
        if not out or "No player" in out:
            return None
        parts = out.split("|")
        return {
            "title":  parts[0] if parts else "",
            "artist": parts[1] if len(parts) > 1 else "",
            "album":  parts[2] if len(parts) > 2 else "",
            "app":    "playerctl",
            "status": parts[3].title() if len(parts) > 3 else "Playing",
        }
    except FileNotFoundError:
        return None
    except Exception:
        return None


def _linux_control(action: str) -> bool:
    cmd_map = {"play_pause": "play-pause", "next": "next", "prev": "previous"}
    cmd = cmd_map.get(action)
    if not cmd:
        return False
    try:
        subprocess.run(["playerctl", cmd], capture_output=True, timeout=3)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════

def get_media_info() -> dict | None:
    """Return current media info dict or None if nothing is playing.

    Keys: title, artist, album, app, status ("Playing" | "Paused")
    """
    if _OS == "Windows":
        return _win_get()
    if _OS == "Darwin":
        return _mac_get()
    if _OS == "Linux":
        return _linux_get()
    return None


def media_control(action: str) -> bool:
    """Send a transport command: 'play_pause' | 'next' | 'prev'."""
    if _OS == "Windows":
        return _win_control(action)
    if _OS == "Darwin":
        return _mac_control(action)
    if _OS == "Linux":
        return _linux_control(action)
    return False
