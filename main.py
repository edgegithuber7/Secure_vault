"""
main.py – SecureVault v3 — Feature-rich Bitwarden-style password manager.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from PySide6.QtCore import Qt, QRect, QTimer, QPoint, Signal, QDate
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QListWidget, QComboBox, QCheckBox,
    QTextEdit, QScrollArea, QFrame, QSpinBox, QProgressBar, QFileDialog,
    QMessageBox, QHBoxLayout, QVBoxLayout, QDateEdit,
    QTabWidget, QDialog, QMenu,
)

from vault_storage import VaultStorage
from Vault_details import ItemDetails, ITEM_TYPES
from Generator import PasswordGenerator
from password_strength import PasswordStrength
from updater import UpdateChecker, APP_VERSION

try:
    from now_playing import get_media_info, media_control
except ImportError:
    def get_media_info(): return None  # type: ignore[misc]
    def media_control(_): return False  # type: ignore[misc]

# ── Palette ────────────────────────────────────────────────────────────
SB       = "rgb(10,12,32)"
BG       = "rgb(17,21,46)"
CARD     = "rgb(26,32,60)"
CARD_H   = "rgb(32,40,72)"
ACCENT   = "rgb(99,102,241)"
ACCENT_H = "rgb(118,121,255)"
TEXT     = "rgb(226,232,240)"
TEXT2    = "rgb(148,163,184)"
MUTED    = "rgb(100,116,139)"
INP      = "rgb(22,28,54)"
BORDER   = "rgb(51,65,85)"
BDR_L    = "rgb(71,85,105)"
OK       = "rgb(16,185,129)"
ERR      = "rgb(239,68,68)"
WARN     = "rgb(245,158,11)"
INFO     = "rgb(56,189,248)"

TYPE_COLORS = {
    "login":    "rgb(99,102,241)",
    "note":     "rgb(16,185,129)",
    "card":     "rgb(245,158,11)",
    "identity": "rgb(236,72,153)",
}
TYPE_ICONS = {"login": "🔑", "note": "📝", "card": "💳", "identity": "👤"}

SORT_OPTIONS = [
    ("name_asc",  "Name A → Z"),
    ("name_desc", "Name Z → A"),
    ("date_desc", "Newest First"),
    ("date_asc",  "Oldest First"),
    ("type",      "By Type"),
]

ACCENT_PRESETS = {
    "indigo": "rgb(99,102,241)",
    "violet": "rgb(139,92,246)",
    "sky":    "rgb(14,165,233)",
    "emerald":"rgb(16,185,129)",
    "rose":   "rgb(244,63,94)",
    "amber":  "rgb(245,158,11)",
}


# ── Tiny helpers ───────────────────────────────────────────────────────

def _rgba(rgb: str, a: float) -> str:
    return rgb.replace("rgb(", "rgba(").replace(")", f", {a})")


def _f(size=13, bold=False, mono=False) -> QFont:
    f = QFont("Consolas" if mono else "Segoe UI", size)
    f.setBold(bold)
    return f


def _lbl(parent, text, x=0, y=0, w=200, h=24, colour=TEXT, size=13, bold=False,
         align=Qt.AlignLeft | Qt.AlignVCenter, wrap=False) -> QLabel:
    l = QLabel(text, parent)
    if x or y or w or h:
        l.setGeometry(QRect(x, y, w, h))
    l.setFont(_f(size, bold))
    l.setStyleSheet(f"color: {colour}; background: transparent;")
    l.setAlignment(align)
    if wrap:
        l.setWordWrap(True)
    return l


def _inp(parent, x, y, w, h, placeholder="", password=False, mono=False) -> QLineEdit:
    le = QLineEdit(parent)
    le.setGeometry(QRect(x, y, w, h))
    le.setPlaceholderText(placeholder)
    if password:
        le.setEchoMode(QLineEdit.Password)
    le.setFont(_f(13, mono=mono))
    le.setStyleSheet(f"""
        QLineEdit {{
            background: {INP}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 8px; padding: 0 12px;
        }}
        QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
    """)
    return le


def _btn(parent, text, x, y, w, h, style="primary", radius=8) -> QPushButton:
    b = QPushButton(text, parent)
    b.setGeometry(QRect(x, y, w, h))
    b.setCursor(Qt.PointingHandCursor)
    b.setFont(_f(13, bold=(style == "primary")))
    styles = {
        "primary": f"""
            QPushButton {{ background: {ACCENT}; color: white; border-radius: {radius}px; border: none; }}
            QPushButton:hover {{ background: {ACCENT_H}; }}
            QPushButton:pressed {{ background: rgb(75,75,200); }}""",
        "outline": f"""
            QPushButton {{ background: transparent; color: {ACCENT}; border: 1px solid {ACCENT}; border-radius: {radius}px; }}
            QPushButton:hover {{ background: {_rgba(ACCENT, 0.12)}; }}""",
        "ghost": f"""
            QPushButton {{ background: transparent; color: {TEXT2}; border: none; border-radius: {radius}px; }}
            QPushButton:hover {{ background: {_rgba(ACCENT, 0.10)}; color: {TEXT}; }}""",
        "danger": f"""
            QPushButton {{ background: {ERR}; color: white; border-radius: {radius}px; border: none; font-weight: bold; }}
            QPushButton:hover {{ background: rgb(220,40,40); }}""",
        "success": f"""
            QPushButton {{ background: {OK}; color: white; border-radius: {radius}px; border: none; font-weight: bold; }}
            QPushButton:hover {{ background: rgb(5,150,100); }}""",
    }
    b.setStyleSheet(styles.get(style, styles["primary"]))
    return b


def _sb_btn(parent, text, x, y, w=218, h=36, icon="") -> QPushButton:
    label = f"  {icon}  {text}" if icon else f"     {text}"
    b = QPushButton(label, parent)
    b.setGeometry(QRect(x, y, w, h))
    b.setCursor(Qt.PointingHandCursor)
    b.setCheckable(True)
    b.setFont(_f(13))
    b.setStyleSheet(f"""
        QPushButton {{
            background: transparent; color: {MUTED};
            border: none; border-radius: 8px;
            text-align: left; padding-left: 4px;
        }}
        QPushButton:hover {{ background: {_rgba(ACCENT, 0.10)}; color: {TEXT}; }}
        QPushButton:checked {{
            background: {_rgba(ACCENT, 0.20)}; color: {TEXT}; font-weight: bold;
        }}
    """)
    return b


def _cmb(parent, items, x, y, w, h) -> QComboBox:
    c = QComboBox(parent)
    c.setGeometry(QRect(x, y, w, h))
    c.addItems(items)
    c.setFont(_f(12))
    c.setStyleSheet(f"""
        QComboBox {{
            background: {INP}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 8px; padding: 0 10px;
        }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{
            background: {CARD}; color: {TEXT};
            border: 1px solid {BORDER};
            selection-background-color: {ACCENT};
        }}
    """)
    return c


def _textedit(parent, x, y, w, h, placeholder="") -> QTextEdit:
    te = QTextEdit(parent)
    te.setGeometry(QRect(x, y, w, h))
    te.setPlaceholderText(placeholder)
    te.setFont(_f(13))
    te.setStyleSheet(f"""
        QTextEdit {{
            background: {INP}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 8px; padding: 8px;
        }}
        QTextEdit:focus {{ border: 1px solid {ACCENT}; }}
    """)
    return te


def _separator(parent, x, y, w=218, h=1) -> QFrame:
    sep = QFrame(parent)
    sep.setGeometry(QRect(x, y, w, h))
    sep.setStyleSheet(f"background: {BORDER};")
    return sep


def _section_lbl(parent, text, x, y) -> QLabel:
    return _lbl(parent, text, x, y, 218, 18, colour=MUTED, size=9, bold=True)


def _spinbox(parent, x, y, w, h, lo=0, hi=100, val=0) -> QSpinBox:
    s = QSpinBox(parent)
    s.setGeometry(QRect(x, y, w, h))
    s.setRange(lo, hi)
    s.setValue(val)
    s.setFont(_f(13))
    s.setStyleSheet(f"""
        QSpinBox {{
            background: {INP}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 8px; padding: 0 8px;
        }}
    """)
    return s


# ── Item card ──────────────────────────────────────────────────────────

class ItemCard(QFrame):
    """Rich vault-item card. Emits `opened` (left-click) and `menu` (right-click)."""

    opened = Signal(str)            # item_id
    menu   = Signal(str, QPoint)    # item_id, global pos

    def __init__(self, item: dict, copy_pw_fn, copy_user_fn, parent=None):
        super().__init__(parent)
        self._item_id = item.get("id", "")
        item_type = item.get("item_type", "login")
        colour    = TYPE_COLORS.get(item_type, ACCENT)
        icon      = TYPE_ICONS.get(item_type, "🔑")
        name      = item.get("item_name", "(Unnamed)")
        sub       = (item.get("username") or item.get("website") or
                     f"{item.get('first_name','')} {item.get('last_name','')}".strip() or
                     item.get("card_holder", ""))
        tags      = item.get("tags", [])
        is_fav    = item.get("favourite", False)

        try:
            expired = ItemDetails.from_dict(item).is_expired()
        except Exception:
            expired = False

        self.setFixedHeight(76)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            ItemCard {{
                background: {CARD};
                border-radius: 10px;
                border: 1px solid {BORDER};
                border-left: 3px solid {colour};
            }}
            ItemCard:hover {{
                background: {CARD_H};
                border: 1px solid {BDR_L};
                border-left: 3px solid {colour};
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 0, 12, 0)
        row.setSpacing(10)

        # Type badge
        badge = QLabel(icon)
        badge.setFixedSize(40, 40)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFont(_f(17))
        badge.setStyleSheet(f"background: {_rgba(colour, 0.15)}; border-radius: 20px;")
        row.addWidget(badge)

        # Info column
        info = QWidget()
        info.setStyleSheet("background: transparent;")
        info_vl = QVBoxLayout(info)
        info_vl.setContentsMargins(0, 10, 0, 10)
        info_vl.setSpacing(3)

        # Name row
        name_w = QWidget()
        name_w.setStyleSheet("background: transparent;")
        name_hl = QHBoxLayout(name_w)
        name_hl.setContentsMargins(0, 0, 0, 0)
        name_hl.setSpacing(5)

        lbl_n = QLabel(name)
        lbl_n.setFont(_f(13, bold=True))
        lbl_n.setStyleSheet(f"color: {TEXT};")
        name_hl.addWidget(lbl_n)

        if is_fav:
            s = QLabel("★")
            s.setStyleSheet(f"color: {WARN}; font-size: 12px;")
            name_hl.addWidget(s)

        if expired:
            e = QLabel("EXPIRED")
            e.setStyleSheet(f"color: white; background: {ERR}; border-radius: 4px; padding: 1px 5px; font-size: 9px; font-weight: bold;")
            name_hl.addWidget(e)

        name_hl.addStretch()
        info_vl.addWidget(name_w)

        lbl_s = QLabel(sub or ITEM_TYPES.get(item_type, ""))
        lbl_s.setFont(_f(11))
        lbl_s.setStyleSheet(f"color: {MUTED};")
        info_vl.addWidget(lbl_s)

        if tags:
            t_w = QWidget()
            t_w.setStyleSheet("background: transparent;")
            t_hl = QHBoxLayout(t_w)
            t_hl.setContentsMargins(0, 0, 0, 0)
            t_hl.setSpacing(4)
            for tag in tags[:3]:
                tl = QLabel(tag)
                tl.setStyleSheet(f"color: {TEXT2}; background: {INP}; border-radius: 4px; padding: 1px 7px; font-size: 10px;")
                t_hl.addWidget(tl)
            t_hl.addStretch()
            info_vl.addWidget(t_w)

        row.addWidget(info, stretch=1)

        # Quick copy buttons (login only) – these are QPushButtons so they absorb
        # mouse events themselves and never trigger this card's mousePressEvent.
        if item_type == "login":
            for label, tooltip, val in [
                ("🔑", "Copy password", item.get("password", "")),
                ("👤", "Copy username", item.get("username", "")),
            ]:
                b = QPushButton(label)
                b.setFixedSize(30, 30)
                b.setToolTip(tooltip)
                b.setCursor(Qt.PointingHandCursor)
                b.setStyleSheet(f"""
                    QPushButton {{ background: transparent; border: none; font-size: 13px; border-radius: 6px; }}
                    QPushButton:hover {{ background: {INP}; }}
                """)
                captured_val = val
                if "password" in tooltip.lower():
                    b.clicked.connect(lambda _=False, v=captured_val: copy_pw_fn(v))
                else:
                    b.clicked.connect(lambda _=False, v=captured_val: copy_user_fn(v))
                row.addWidget(b)

        # Make every non-button child transparent to mouse events so that
        # clicks anywhere on the card body reach this QFrame's mousePressEvent.
        for child in self.findChildren(QWidget):
            if not isinstance(child, QPushButton):
                child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.opened.emit(self._item_id)
        elif event.button() == Qt.RightButton:
            self.menu.emit(self._item_id, event.globalPosition().toPoint())
        super().mousePressEvent(event)


# ── Password history dialog ────────────────────────────────────────────

class PasswordHistoryDialog(QDialog):
    def __init__(self, history: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Password History")
        self.setFixedSize(560, 420)
        self.setStyleSheet(f"background: {BG}; color: {TEXT};")

        vl = QVBoxLayout(self)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(10)

        title = QLabel("Password History (last 10)")
        title.setFont(_f(15, bold=True))
        title.setStyleSheet(f"color: {TEXT};")
        vl.addWidget(title)

        if not history:
            lbl = QLabel("No password history recorded.")
            lbl.setStyleSheet(f"color: {MUTED};")
            vl.addWidget(lbl)
        else:
            for entry in history:
                row = QFrame()
                row.setStyleSheet(f"background: {CARD}; border-radius: 8px; border: 1px solid {BORDER};")
                rl = QHBoxLayout(row)
                rl.setContentsMargins(12, 8, 12, 8)

                changed = entry.get("changed", "")
                try:
                    dt = datetime.fromisoformat(changed)
                    changed_str = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    changed_str = changed

                pw_lbl = QLabel(entry.get("password", ""))
                pw_lbl.setFont(_f(13, mono=True))
                pw_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
                rl.addWidget(pw_lbl, stretch=1)

                date_lbl = QLabel(changed_str)
                date_lbl.setFont(_f(11))
                date_lbl.setStyleSheet(f"color: {MUTED}; background: transparent;")
                rl.addWidget(date_lbl)

                btn_copy = QPushButton("Copy")
                btn_copy.setFixedSize(60, 26)
                btn_copy.setCursor(Qt.PointingHandCursor)
                btn_copy.setStyleSheet(f"""
                    QPushButton {{ background: {_rgba(ACCENT, 0.2)}; color: {ACCENT}; border-radius: 6px; border: none; font-size: 11px; }}
                    QPushButton:hover {{ background: {ACCENT}; color: white; }}
                """)
                pw = entry.get("password", "")
                btn_copy.clicked.connect(lambda _=False, v=pw: QApplication.clipboard().setText(v))
                rl.addWidget(btn_copy)

                vl.addWidget(row)

        vl.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT}; color: white; border-radius: 8px; padding: 6px 0; font-weight: bold; }}
            QPushButton:hover {{ background: {ACCENT_H}; }}
        """)
        close_btn.clicked.connect(self.accept)
        vl.addWidget(close_btn, alignment=Qt.AlignRight)


# ══════════════════════════════════════════════════════════════════════
# Main vault window
# ══════════════════════════════════════════════════════════════════════

class SecureVault(QMainWindow):
    def __init__(self, username: str, master_password: str):
        super().__init__()
        self.username        = username
        self.storage         = VaultStorage(username, master_password)
        self.generator       = PasswordGenerator()
        self._current_id: str | None = None
        self._pw_visible     = False
        self._filter_type    = "all"
        self._filter_folder  = ""
        self._show_favs      = False
        self._show_recent    = False
        self._current_sort   = self.storage.get_settings().get("default_sort", "name_asc")
        self._clipboard_val  = ""
        self._lock_timer     = QTimer(self)
        self._lock_timer.timeout.connect(self._auto_lock)
        self._clip_timer     = QTimer(self)
        self._clip_timer.setSingleShot(True)
        self._clip_timer.timeout.connect(self._clear_clipboard)
        self._clip_secs      = 0
        self._clip_remaining = 0
        self._np_timer       = QTimer(self)
        self._np_timer.timeout.connect(self._refresh_np_mini)

        self.setWindowTitle(f"SecureVault — {username}")
        self.setFixedSize(1280, 870)
        self.setStyleSheet(f"background: {SB};")

        self.central = QWidget(self)
        self.setCentralWidget(self.central)

        self._build_sidebar()
        self._build_topbar()
        self._build_stack()
        self._build_statusbar()

        self._apply_settings()
        self._nav_to(0)
        self._np_timer.start(3000)
        self._refresh_np_mini()

        # Check for updates 5 s after startup so the window feels snappy first
        QTimer.singleShot(5000, self._start_update_check)

    # ═══════════════════════════════════════════════════════════════════
    # Sidebar
    # ═══════════════════════════════════════════════════════════════════

    def _build_sidebar(self):
        sb = QFrame(self.central)
        sb.setGeometry(QRect(0, 0, 240, 870))
        sb.setObjectName("sidebar")
        sb.setStyleSheet(f"QFrame#sidebar {{ background: {SB}; border-right: 1px solid {BORDER}; }}")

        # Logo
        logo = QLabel("🔐 SecureVault", sb)
        logo.setGeometry(QRect(0, 14, 240, 36))
        logo.setFont(_f(15, bold=True))
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"color: {TEXT}; background: transparent;")

        user_lbl = QLabel(f"@{self.username}", sb)
        user_lbl.setGeometry(QRect(0, 50, 240, 20))
        user_lbl.setFont(_f(10))
        user_lbl.setAlignment(Qt.AlignCenter)
        user_lbl.setStyleSheet(f"color: {MUTED}; background: transparent;")

        _separator(sb, 10, 78, 220)

        y = 88
        self.btnAll      = _sb_btn(sb, "All Items",       10, y, icon="")  ; y += 36
        self.btnFavs     = _sb_btn(sb, "Favourites",      10, y, icon="★") ; y += 36
        self.btnRecent   = _sb_btn(sb, "Recently Added",  10, y, icon="🕐") ; y += 36

        self.btnAll.clicked.connect(lambda:    self._set_filter("all", "", False, False))
        self.btnFavs.clicked.connect(lambda:   self._set_filter("all", "", True, False))
        self.btnRecent.clicked.connect(lambda: self._set_filter("all", "", False, True))

        y += 4
        _separator(sb, 10, y, 220) ; y += 8
        _section_lbl(sb, "TYPES", 18, y) ; y += 20

        self.btnLogin    = _sb_btn(sb, "Logins",          10, y, icon="🔑") ; y += 35
        self.btnNote     = _sb_btn(sb, "Secure Notes",    10, y, icon="📝") ; y += 35
        self.btnCard     = _sb_btn(sb, "Cards",           10, y, icon="💳") ; y += 35
        self.btnIdentity = _sb_btn(sb, "Identities",      10, y, icon="👤") ; y += 35

        self.btnLogin.clicked.connect(lambda:    self._set_filter("login",    "", False, False))
        self.btnNote.clicked.connect(lambda:     self._set_filter("note",     "", False, False))
        self.btnCard.clicked.connect(lambda:     self._set_filter("card",     "", False, False))
        self.btnIdentity.clicked.connect(lambda: self._set_filter("identity", "", False, False))

        y += 4
        _separator(sb, 10, y, 220) ; y += 8
        _section_lbl(sb, "TOOLS", 18, y) ; y += 20

        self.btnDashboard  = _sb_btn(sb, "Dashboard",     10, y, icon="📊") ; y += 35
        self.btnGenerator  = _sb_btn(sb, "Generator",     10, y, icon="⚙")  ; y += 35
        self.btnNowPlaying = _sb_btn(sb, "Now Playing",   10, y, icon="🎵") ; y += 35
        self.btnSettings   = _sb_btn(sb, "Settings",      10, y, icon="⚙️") ; y += 35

        self.btnDashboard.clicked.connect(lambda:  self._nav_to(2))
        self.btnGenerator.clicked.connect(lambda:  self._nav_to(3))
        self.btnNowPlaying.clicked.connect(lambda: self._nav_to(5))
        self.btnSettings.clicked.connect(lambda:   self._nav_to(4))

        self._sb_btns = [
            self.btnAll, self.btnFavs, self.btnRecent,
            self.btnLogin, self.btnNote, self.btnCard, self.btnIdentity,
            self.btnDashboard, self.btnGenerator, self.btnNowPlaying, self.btnSettings,
        ]

        # Now Playing mini widget
        _separator(sb, 10, 718, 220)
        self.npMini = QFrame(sb)
        self.npMini.setGeometry(QRect(8, 724, 224, 88))
        self.npMini.setStyleSheet(f"""
            QFrame {{ background: {CARD}; border-radius: 10px; border: 1px solid {BORDER}; }}
        """)

        self.npTitle  = _lbl(self.npMini, "Nothing playing",  8, 8,  208, 18, colour=TEXT,  size=11, bold=True)
        self.npArtist = _lbl(self.npMini, "",                  8, 28, 208, 16, colour=MUTED, size=10)
        self.npApp    = _lbl(self.npMini, "",                  8, 46, 140, 14, colour=INFO,  size=9)

        # Controls
        ctrl_y = 62
        for label, action, cx in [("⏮", "prev", 8), ("⏯", "play_pause", 50), ("⏭", "next", 92)]:
            b = QPushButton(label, self.npMini)
            b.setGeometry(QRect(cx, ctrl_y, 36, 22))
            b.setCursor(Qt.PointingHandCursor)
            b.setFont(_f(12))
            b.setStyleSheet(f"""
                QPushButton {{ background: {INP}; color: {TEXT}; border: none; border-radius: 6px; }}
                QPushButton:hover {{ background: {ACCENT}; }}
            """)
            act = action
            b.clicked.connect(lambda _=False, a=act: media_control(a))

        _separator(sb, 10, 820, 220)
        btn_lock = _btn(sb, "🔒  Lock Vault", 10, 828, 220, 34, style="ghost")
        btn_lock.clicked.connect(self._lock_vault)

    # ═══════════════════════════════════════════════════════════════════
    # Top bar
    # ═══════════════════════════════════════════════════════════════════

    def _build_topbar(self):
        tb = QFrame(self.central)
        tb.setGeometry(QRect(240, 0, 1040, 66))
        tb.setStyleSheet(f"background: {BG}; border-bottom: 1px solid {BORDER};")

        self.leSearch = QLineEdit(tb)
        self.leSearch.setGeometry(QRect(20, 14, 460, 38))
        self.leSearch.setPlaceholderText("🔍  Search vault…")
        self.leSearch.setFont(_f(13))
        self.leSearch.setStyleSheet(f"""
            QLineEdit {{
                background: {INP}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 19px; padding: 0 18px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
        """)
        self.leSearch.textChanged.connect(self._on_search)

        sort_labels = [v for _, v in SORT_OPTIONS]
        self.cmbSort = _cmb(tb, sort_labels, 498, 16, 180, 34)
        self.cmbSort.currentIndexChanged.connect(self._on_sort_changed)

        btn_add = _btn(tb, "+ Add Item", 698, 16, 120, 34)
        btn_add.clicked.connect(self._new_item)

        # Keyboard shortcuts
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._new_item)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: (self._nav_to(0), self.leSearch.setFocus()))
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._lock_vault)
        QShortcut(QKeySequence("Escape"), self).activated.connect(lambda: self.stack.currentIndex() == 1 and self._back_to_list())

    # ═══════════════════════════════════════════════════════════════════
    # Stacked pages
    # ═══════════════════════════════════════════════════════════════════

    def _build_stack(self):
        self.stack = QStackedWidget(self.central)
        self.stack.setGeometry(QRect(240, 66, 1040, 774))
        self.stack.setStyleSheet(f"background: {BG};")

        self.stack.addWidget(self._page_list())       # 0
        self.stack.addWidget(self._page_edit())       # 1
        self.stack.addWidget(self._page_dashboard())  # 2
        self.stack.addWidget(self._page_generator())  # 3
        self.stack.addWidget(self._page_settings())   # 4
        self.stack.addWidget(self._page_now_playing())# 5

    # ── Page 0: List ────────────────────────────────────────────────────

    def _page_list(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {BG};")

        self.lblListTitle = _lbl(page, "All Items", 22, 16, 700, 32, size=18, bold=True)

        self._list_scroll = QScrollArea(page)
        self._list_scroll.setGeometry(QRect(12, 56, 1016, 710))
        self._list_scroll.setWidgetResizable(True)
        self._list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list_scroll.setStyleSheet(f"""
            QScrollArea {{ background: {BG}; border: none; }}
            QScrollBar:vertical {{ background: {BG}; width: 8px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._items_widget = QWidget()
        self._items_widget.setStyleSheet(f"background: {BG};")
        self._items_layout = QVBoxLayout(self._items_widget)
        self._items_layout.setContentsMargins(4, 4, 4, 4)
        self._items_layout.setSpacing(5)
        self._list_scroll.setWidget(self._items_widget)

        return page

    # ── Page 1: Edit/Add ────────────────────────────────────────────────

    def _page_edit(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {BG};")

        scroll = QScrollArea(page)
        scroll.setGeometry(QRect(0, 0, 1040, 774))
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {BG}; }}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setStyleSheet(f"background: {BG};")
        scroll.setWidget(inner)

        px, pw = 28, 970

        self.btnEditBack = _btn(inner, "← Back", px, 16, 80, 32, style="ghost")
        self.btnEditBack.clicked.connect(self._back_to_list)

        self.lblEditTitle = _lbl(inner, "Add Item", px + 90, 16, 600, 32, size=18, bold=True)

        # Type + folder row
        _lbl(inner, "Item Type", px, 65, 140, 22, colour=TEXT2, size=11)
        self.cmbType = _cmb(inner, list(ITEM_TYPES.values()), px, 88, 190, 40)
        self.cmbType.currentIndexChanged.connect(self._on_type_changed)

        _lbl(inner, "Folder", px + 210, 65, 140, 22, colour=TEXT2, size=11)
        self.cmbFolder = _cmb(inner, ["(None)"], px + 210, 88, 190, 40)

        self.cbFavourite = QCheckBox("★  Favourite", inner)
        self.cbFavourite.setGeometry(QRect(px + 420, 96, 160, 28))
        self.cbFavourite.setFont(_f(13))
        self.cbFavourite.setStyleSheet(f"color: {WARN}; background: transparent;")

        _lbl(inner, "Name *", px, 144, 200, 22, colour=TEXT2, size=11)
        self.leItemName = _inp(inner, px, 168, pw, 42, "Item name")

        # ── Login fields ─────────────────────────────────────────────
        self.frameLogin = QFrame(inner)
        self.frameLogin.setGeometry(QRect(px, 226, pw, 360))
        self.frameLogin.setStyleSheet("background: transparent;")

        _lbl(self.frameLogin, "Username / Email", 0, 0, 300, 22, colour=TEXT2, size=11)
        self.leUsername = _inp(self.frameLogin, 0, 24, pw, 42, "Username or email")

        _lbl(self.frameLogin, "Password", 0, 82, 300, 22, colour=TEXT2, size=11)
        self.lePassword = _inp(self.frameLogin, 0, 106, pw - 210, 42, "Password", password=True, mono=True)

        self.btnTogglePw = _btn(self.frameLogin, "Show", pw - 202, 106, 58, 42, style="ghost")
        self.btnTogglePw.clicked.connect(self._toggle_pw_visible)

        self.btnGenPw = _btn(self.frameLogin, "⚡ Gen", pw - 138, 106, 72, 42, style="outline")
        self.btnGenPw.clicked.connect(self._quick_generate)

        self.btnHistPw = _btn(self.frameLogin, "📋 History", pw - 60, 106, 62, 42, style="ghost")
        self.btnHistPw.clicked.connect(self._show_pw_history)

        # Strength bar
        self.pbStrength = QProgressBar(self.frameLogin)
        self.pbStrength.setGeometry(QRect(0, 154, pw, 6))
        self.pbStrength.setTextVisible(False)
        self.pbStrength.setStyleSheet(f"QProgressBar {{ background: {BORDER}; border-radius: 3px; }} QProgressBar::chunk {{ background: {OK}; border-radius: 3px; }}")
        self.lblStrength = _lbl(self.frameLogin, "", 0, 162, pw, 18, colour=MUTED, size=11)
        self.lePassword.textChanged.connect(self._update_strength)

        _lbl(self.frameLogin, "Website", 0, 188, 300, 22, colour=TEXT2, size=11)
        self.leWebsite = _inp(self.frameLogin, 0, 212, pw, 42, "https://")

        _lbl(self.frameLogin, "TOTP Secret (2FA)", 0, 270, 300, 22, colour=TEXT2, size=11)
        self.leTotp = _inp(self.frameLogin, 0, 294, pw - 100, 42, "Base32 secret key (e.g. JBSWY3DPEHPK3PXP)")

        _lbl(self.frameLogin, "Expiry Date", 0, 352, 200, 22, colour=TEXT2, size=11)
        self.dteExpiry = QDateEdit(self.frameLogin)
        self.dteExpiry.setGeometry(QRect(0, 376, 200, 42))
        self.dteExpiry.setCalendarPopup(True)
        self.dteExpiry.setDisplayFormat("dd/MM/yyyy")
        self.dteExpiry.setSpecialValueText("No expiry")
        self.dteExpiry.setMinimumDate(QDate(2000, 1, 1))
        self.dteExpiry.setStyleSheet(f"QDateEdit {{ background: {INP}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 0 10px; font-size: 13px; }}")

        # ── Card fields ──────────────────────────────────────────────
        self.frameCard = QFrame(inner)
        self.frameCard.setGeometry(QRect(px, 226, pw, 300))
        self.frameCard.setStyleSheet("background: transparent;")

        _lbl(self.frameCard, "Cardholder Name", 0, 0, 400, 22, colour=TEXT2, size=11)
        self.leCardHolder = _inp(self.frameCard, 0, 24, pw, 42, "Name on card")

        _lbl(self.frameCard, "Card Number", 0, 82, 400, 22, colour=TEXT2, size=11)
        self.leCardNumber = _inp(self.frameCard, 0, 106, pw, 42, "•••• •••• •••• ••••", mono=True)

        _lbl(self.frameCard, "Brand", 0, 164, 150, 22, colour=TEXT2, size=11)
        self.leCardBrand = _inp(self.frameCard, 0, 188, 200, 42, "Visa / Mastercard…")

        _lbl(self.frameCard, "Expiry (MM/YY)", 220, 164, 200, 22, colour=TEXT2, size=11)
        self.leCardExpiry = _inp(self.frameCard, 220, 188, 160, 42, "MM/YY")

        _lbl(self.frameCard, "CVV", 400, 164, 100, 22, colour=TEXT2, size=11)
        self.leCardCvv = _inp(self.frameCard, 400, 188, 100, 42, "•••")

        # ── Identity fields ──────────────────────────────────────────
        self.frameIdentity = QFrame(inner)
        self.frameIdentity.setGeometry(QRect(px, 226, pw, 310))
        self.frameIdentity.setStyleSheet("background: transparent;")

        _lbl(self.frameIdentity, "First Name", 0, 0, 300, 22, colour=TEXT2, size=11)
        self.leFirstName = _inp(self.frameIdentity, 0, 24, 470, 42)
        _lbl(self.frameIdentity, "Last Name", 490, 0, 300, 22, colour=TEXT2, size=11)
        self.leLastName = _inp(self.frameIdentity, 490, 24, 470, 42)

        _lbl(self.frameIdentity, "Email", 0, 82, 300, 22, colour=TEXT2, size=11)
        self.leEmail = _inp(self.frameIdentity, 0, 106, pw, 42)
        _lbl(self.frameIdentity, "Phone", 0, 164, 300, 22, colour=TEXT2, size=11)
        self.lePhone = _inp(self.frameIdentity, 0, 188, 320, 42)
        _lbl(self.frameIdentity, "Address", 0, 246, 300, 22, colour=TEXT2, size=11)
        self.leAddress = _inp(self.frameIdentity, 0, 270, pw, 42)

        # ── Shared: Notes & Tags ─────────────────────────────────────
        _lbl(inner, "Notes", px, 606, 400, 22, colour=TEXT2, size=11)
        self.teNotes = _textedit(inner, px, 630, pw, 90, "Additional notes…")

        _lbl(inner, "Tags  (comma separated)", px, 732, 400, 22, colour=TEXT2, size=11)
        self.leTags = _inp(inner, px, 756, pw, 42, "work, banking, 2fa…")

        # Action bar
        self.btnSave      = _btn(inner, "💾  Save", px, 816, 150, 44)
        self.btnDuplicate = _btn(inner, "⎘  Duplicate", px + 160, 816, 140, 44, style="outline")
        self.btnDelete    = _btn(inner, "Delete", pw - 80, 816, 110, 44, style="danger")
        self.btnSave.clicked.connect(self._save_item)
        self.btnDuplicate.clicked.connect(self._duplicate_item)
        self.btnDelete.clicked.connect(self._delete_item)

        self.lblEditStatus = _lbl(inner, "", px, 872, pw, 22, colour=OK, size=11)
        inner.setMinimumHeight(910)
        self._on_type_changed(0)
        return page

    # ── Page 2: Dashboard ───────────────────────────────────────────────

    def _page_dashboard(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {BG};")

        _lbl(page, "Password Health Dashboard", 22, 16, 700, 32, size=18, bold=True)
        btn_r = _btn(page, "Refresh", 950, 16, 80, 32, style="ghost")
        btn_r.clicked.connect(self._refresh_dashboard)

        # Stat cards row
        def _stat(parent, x, y, title, colour=ACCENT) -> tuple:
            f = QFrame(parent)
            f.setGeometry(QRect(x, y, 228, 90))
            f.setStyleSheet(f"background: {CARD}; border-radius: 12px; border-left: 3px solid {colour}; border-top: none; border-right: none; border-bottom: none;")
            _lbl(f, title, 14, 10, 200, 18, colour=MUTED, size=10)
            v = _lbl(f, "—", 14, 30, 200, 40, size=28, bold=True)
            s = _lbl(f, "", 14, 68, 200, 18, colour=MUTED, size=10)
            return v, s

        x0 = 16
        self.lblDTotal,    _   = _stat(page, x0,           70, "Total Items",            INFO)
        self.lblDLogins,   _   = _stat(page, x0 + 234,     70, "Logins",                 TYPE_COLORS["login"])
        self.lblDNotes,    _   = _stat(page, x0 + 234 * 2, 70, "Secure Notes",           TYPE_COLORS["note"])
        self.lblDCards,    _   = _stat(page, x0 + 234 * 3, 70, "Cards",                  TYPE_COLORS["card"])
        self.lblDScore,    _   = _stat(page, x0 + 234 * 4 - 6, 70, "Vault Health Score", OK)

        _lbl(page, "Overall Security Score", 22, 178, 300, 22, bold=True)
        self.pbScore = QProgressBar(page)
        self.pbScore.setGeometry(QRect(22, 204, 1010, 16))
        self.pbScore.setTextVisible(True)
        self.pbScore.setFont(_f(10))
        self.pbScore.setStyleSheet(f"""
            QProgressBar {{ background: {BORDER}; border-radius: 8px; color: white; }}
            QProgressBar::chunk {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {TYPE_COLORS['login']}, stop:1 {OK}); border-radius: 8px; }}
        """)

        # Issue lists
        def _issue_list(parent, x, y, w, h, title) -> tuple:
            _lbl(parent, title, x, y, w, 22, bold=True)
            lw = QListWidget(parent)
            lw.setGeometry(QRect(x, y + 26, w, h))
            lw.setStyleSheet(f"""
                QListWidget {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; color: {TEXT}; font-size: 12px; outline: none; }}
                QListWidget::item {{ padding: 6px 12px; }}
                QListWidget::item:selected {{ background: {_rgba(ACCENT, 0.2)}; }}
            """)
            return lw

        self.lwWeak   = _issue_list(page, 16,  236, 490, 200, f"⚠  Weak Passwords")
        self.lwReused = _issue_list(page, 524, 236, 490, 200, f"♻  Reused Passwords")
        self.lwOld    = _issue_list(page, 16,  480, 1008, 180, "🕐  Old Passwords (unchanged 1+ year)")

        return page

    # ── Page 3: Generator ───────────────────────────────────────────────

    def _page_generator(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {BG};")

        _lbl(page, "Password Generator", 22, 16, 600, 32, size=18, bold=True)

        # Output
        self.leGenOut = QLineEdit(page)
        self.leGenOut.setGeometry(QRect(22, 60, 880, 60))
        self.leGenOut.setReadOnly(True)
        self.leGenOut.setFont(_f(20, mono=True))
        self.leGenOut.setAlignment(Qt.AlignCenter)
        self.leGenOut.setStyleSheet(f"""
            QLineEdit {{
                background: {CARD}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 12px; padding: 0 20px;
                letter-spacing: 2px;
            }}
        """)
        btn_copy_gen = _btn(page, "Copy", 912, 68, 78, 44)
        btn_copy_gen.clicked.connect(self._copy_generated)
        btn_regen = _btn(page, "↺", 1000, 68, 32, 44, style="ghost")
        btn_regen.clicked.connect(self._run_generator)

        # Strength
        self.pbGenStr = QProgressBar(page)
        self.pbGenStr.setGeometry(QRect(22, 128, 1010, 6))
        self.pbGenStr.setTextVisible(False)
        self.pbGenStr.setStyleSheet(f"QProgressBar {{ background: {BORDER}; border-radius: 3px; }} QProgressBar::chunk {{ background: {OK}; border-radius: 3px; }}")
        self.lblGenStr = _lbl(page, "", 22, 138, 1010, 18, colour=MUTED, size=11)

        # Mode
        _lbl(page, "Mode", 22, 168, 80, 22, colour=TEXT2, size=11)
        self.cmbGenMode = _cmb(page, ["Password", "Passphrase", "Username"], 22, 192, 200, 40)
        self.cmbGenMode.currentIndexChanged.connect(self._on_gen_mode_changed)

        # Password options frame
        self.fGenPw = QFrame(page)
        self.fGenPw.setGeometry(QRect(22, 248, 1000, 160))
        self.fGenPw.setStyleSheet(f"background: {CARD}; border-radius: 12px; border: 1px solid {BORDER};")

        _lbl(self.fGenPw, "Length", 18, 14, 80, 22, colour=TEXT2, size=11)
        self.sbGenLen = _spinbox(self.fGenPw, 18, 38, 100, 40, lo=4, hi=128, val=20)
        self.sbGenLen.valueChanged.connect(self._run_generator)

        _lbl(self.fGenPw, "Character Sets", 140, 14, 300, 22, colour=TEXT2, size=11)
        cbx_y = 38
        for attr, label, x in [
            ("cbGenLetters", "A-Z Letters",    140),
            ("cbGenNumbers", "0-9 Numbers",    300),
            ("cbGenSpecial", "!@# Symbols",    460),
            ("cbGenAmbig",   "Skip ambiguous", 620),
        ]:
            cb = QCheckBox(label, self.fGenPw)
            cb.setGeometry(QRect(x, cbx_y, 150, 28))
            cb.setChecked(attr != "cbGenAmbig")
            cb.setFont(_f(12))
            cb.setStyleSheet(f"color: {TEXT}; background: transparent;")
            cb.toggled.connect(self._run_generator)
            setattr(self, attr, cb)

        _lbl(self.fGenPw, "Entropy", 140, 78, 300, 18, colour=TEXT2, size=10)
        self.lblGenEntropy = _lbl(self.fGenPw, "—", 140, 96, 300, 22, colour=ACCENT, size=13, bold=True)

        # Passphrase options frame
        self.fGenPhrase = QFrame(page)
        self.fGenPhrase.setGeometry(QRect(22, 248, 1000, 160))
        self.fGenPhrase.setStyleSheet(f"background: {CARD}; border-radius: 12px; border: 1px solid {BORDER};")
        self.fGenPhrase.setVisible(False)

        _lbl(self.fGenPhrase, "Words", 18, 14, 100, 22, colour=TEXT2, size=11)
        self.sbGenWords = _spinbox(self.fGenPhrase, 18, 38, 100, 40, lo=3, hi=10, val=4)
        self.sbGenWords.valueChanged.connect(self._run_generator)

        _lbl(self.fGenPhrase, "Separator", 140, 14, 100, 22, colour=TEXT2, size=11)
        self.lePhrSep = _inp(self.fGenPhrase, 140, 38, 80, 40, "-")
        self.lePhrSep.setText("-")
        self.lePhrSep.textChanged.connect(self._run_generator)

        self.cbPhrCap = QCheckBox("Capitalise", self.fGenPhrase)
        self.cbPhrNum = QCheckBox("Add number", self.fGenPhrase)
        for i, cb in enumerate([self.cbPhrCap, self.cbPhrNum]):
            cb.setGeometry(QRect(250 + i * 150, 46, 140, 28))
            cb.setChecked(True)
            cb.setFont(_f(12))
            cb.setStyleSheet(f"color: {TEXT}; background: transparent;")
            cb.toggled.connect(self._run_generator)

        # History of generated passwords
        _lbl(page, "Generation History", 22, 420, 400, 22, bold=True)
        btn_clear_hist = _btn(page, "Clear", 980, 420, 60, 26, style="ghost")
        btn_clear_hist.clicked.connect(lambda: (self._gen_history.clear(), self._refresh_gen_history()))

        self._gen_history: list[str] = []
        self.lwGenHistory = QListWidget(page)
        self.lwGenHistory.setGeometry(QRect(22, 448, 1010, 260))
        self.lwGenHistory.setStyleSheet(f"""
            QListWidget {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; color: {TEXT}; font-family: Consolas; font-size: 12px; outline: none; }}
            QListWidget::item {{ padding: 6px 14px; }}
            QListWidget::item:hover {{ background: {_rgba(ACCENT, 0.10)}; }}
        """)
        self.lwGenHistory.itemDoubleClicked.connect(lambda li: QApplication.clipboard().setText(li.text().split("  →  ")[0]))

        self._run_generator()
        return page

    # ── Page 4: Settings ────────────────────────────────────────────────

    def _page_settings(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {BG};")

        _lbl(page, "Settings", 22, 16, 400, 32, size=18, bold=True)

        tabs = QTabWidget(page)
        tabs.setGeometry(QRect(16, 58, 1008, 694))
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ background: {BG}; border: none; }}
            QTabBar::tab {{
                background: {CARD}; color: {MUTED}; padding: 8px 20px;
                border-radius: 8px; margin: 2px 2px 0 0;
                font-size: 12px; font-family: 'Segoe UI';
            }}
            QTabBar::tab:selected {{ background: {ACCENT}; color: white; font-weight: bold; }}
            QTabBar::tab:hover {{ background: {CARD_H}; color: {TEXT}; }}
        """)

        tabs.addTab(self._stab_security(), "🔒  Security")
        tabs.addTab(self._stab_vault(),    "🗄  Vault")
        tabs.addTab(self._stab_generator(),"⚙  Generator")
        tabs.addTab(self._stab_appearance(),"🎨  Appearance")
        tabs.addTab(self._stab_data(),     "📂  Data")
        tabs.addTab(self._stab_folders(),  "📁  Folders")

        return page

    def _stab_security(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        _lbl(w, "Auto-Lock After (minutes, 0 = never)", 20, 20, 500, 22, colour=TEXT2, size=11)
        self.sbAutoLock = _spinbox(w, 20, 44, 140, 42, lo=0, hi=120, val=5)

        _lbl(w, "Clipboard Auto-Clear (seconds, 0 = never)", 20, 106, 500, 22, colour=TEXT2, size=11)
        self.sbClipClear = _spinbox(w, 20, 130, 140, 42, lo=0, hi=300, val=30)
        _lbl(w, "Copied passwords are cleared from clipboard after this many seconds.", 20, 178, 700, 18, colour=MUTED, size=10)

        self.cbConfirmDelete = QCheckBox("Confirm before deleting items", w)
        self.cbConfirmDelete.setGeometry(QRect(20, 210, 400, 32))
        self.cbConfirmDelete.setChecked(True)
        self.cbConfirmDelete.setFont(_f(13))
        self.cbConfirmDelete.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self.cbShowPwStrength = QCheckBox("Show password strength bar in edit view", w)
        self.cbShowPwStrength.setGeometry(QRect(20, 250, 500, 32))
        self.cbShowPwStrength.setChecked(True)
        self.cbShowPwStrength.setFont(_f(13))
        self.cbShowPwStrength.setStyleSheet(f"color: {TEXT}; background: transparent;")

        _lbl(w, "⚠  Master password changes require recreating your vault.", 20, 310, 700, 22, colour=WARN, size=11, wrap=True)

        btn_save = _btn(w, "Save Security Settings", 20, 360, 220, 44)
        btn_save.clicked.connect(self._save_settings)
        self.lblSecStatus = _lbl(w, "", 260, 374, 400, 22, colour=OK, size=11)

        return w

    def _stab_vault(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        _lbl(w, "Default Sort Order", 20, 20, 300, 22, colour=TEXT2, size=11)
        self.cmbDefaultSort = _cmb(w, [v for _, v in SORT_OPTIONS], 20, 44, 240, 42)

        _lbl(w, "List Density", 20, 108, 300, 22, colour=TEXT2, size=11)
        self.cmbDensity = _cmb(w, ["Comfortable", "Compact"], 20, 132, 200, 42)

        _lbl(w, "Default Item Type", 20, 196, 300, 22, colour=TEXT2, size=11)
        self.cmbDefaultType = _cmb(w, list(ITEM_TYPES.values()), 20, 220, 200, 42)

        self.cbShowTagsList = QCheckBox("Show tags on list items", w)
        self.cbShowTagsList.setGeometry(QRect(20, 284, 400, 32))
        self.cbShowTagsList.setChecked(True)
        self.cbShowTagsList.setFont(_f(13))
        self.cbShowTagsList.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self.cbWarnExpiry = QCheckBox("Show expiry warnings on list items", w)
        self.cbWarnExpiry.setGeometry(QRect(20, 322, 500, 32))
        self.cbWarnExpiry.setChecked(True)
        self.cbWarnExpiry.setFont(_f(13))
        self.cbWarnExpiry.setStyleSheet(f"color: {TEXT}; background: transparent;")

        btn_save = _btn(w, "Save Vault Settings", 20, 380, 200, 44)
        btn_save.clicked.connect(self._save_settings)
        self.lblVaultStatus = _lbl(w, "", 240, 394, 400, 22, colour=OK, size=11)

        return w

    def _stab_generator(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        _lbl(w, "Default Password Length", 20, 20, 300, 22, colour=TEXT2, size=11)
        self.sbDefLen = _spinbox(w, 20, 44, 140, 42, lo=8, hi=128, val=20)

        self.cbDefLetters = QCheckBox("Include Letters (A-Z)", w)
        self.cbDefNumbers = QCheckBox("Include Numbers (0-9)", w)
        self.cbDefSpecial = QCheckBox("Include Symbols (!@#)", w)
        self.cbDefAmbig   = QCheckBox("Exclude Ambiguous (Il1O0)", w)
        for i, cb in enumerate([self.cbDefLetters, self.cbDefNumbers, self.cbDefSpecial, self.cbDefAmbig]):
            cb.setGeometry(QRect(20, 108 + i * 38, 300, 32))
            cb.setChecked(i < 3)
            cb.setFont(_f(13))
            cb.setStyleSheet(f"color: {TEXT}; background: transparent;")

        _lbl(w, "Passphrase Defaults", 20, 268, 400, 22, colour=TEXT, size=13, bold=True)
        _lbl(w, "Word count", 20, 300, 200, 22, colour=TEXT2, size=11)
        self.sbDefWords = _spinbox(w, 20, 324, 100, 42, lo=3, hi=10, val=4)

        _lbl(w, "Separator", 150, 300, 200, 22, colour=TEXT2, size=11)
        self.leDefSep = _inp(w, 150, 324, 80, 42, "-")
        self.leDefSep.setText("-")

        btn_save = _btn(w, "Save Generator Defaults", 20, 390, 240, 44)
        btn_save.clicked.connect(self._save_settings)
        self.lblGenStatus = _lbl(w, "", 280, 404, 400, 22, colour=OK, size=11)

        return w

    def _stab_appearance(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        _lbl(w, "Accent Colour", 20, 20, 300, 22, colour=TEXT, size=13, bold=True)
        _lbl(w, "Changes apply on next launch.", 20, 48, 400, 18, colour=MUTED, size=10)

        self._accent_btns: list[QPushButton] = []
        for i, (key, rgb) in enumerate(ACCENT_PRESETS.items()):
            b = QPushButton(key.title(), w)
            b.setGeometry(QRect(20 + i * 130, 74, 120, 38))
            b.setCursor(Qt.PointingHandCursor)
            b.setCheckable(True)
            b.setFont(_f(12))
            b.setStyleSheet(f"""
                QPushButton {{ background: {_rgba(rgb, 0.2)}; color: {rgb}; border: 2px solid {_rgba(rgb, 0.4)}; border-radius: 8px; font-weight: bold; }}
                QPushButton:checked {{ background: {rgb}; color: white; border: 2px solid {rgb}; }}
                QPushButton:hover {{ background: {_rgba(rgb, 0.35)}; }}
            """)
            colour_key = key
            b.clicked.connect(lambda _=False, k=colour_key: self._set_accent(k))
            self._accent_btns.append(b)

        _lbl(w, "These settings are visual only and stored per-vault.", 20, 130, 700, 18, colour=MUTED, size=10)

        btn_save = _btn(w, "Save Appearance", 20, 170, 200, 44)
        btn_save.clicked.connect(self._save_settings)
        self.lblAppStatus = _lbl(w, "", 240, 184, 400, 22, colour=OK, size=11)

        return w

    def _stab_data(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        _lbl(w, "Export Vault", 20, 20, 600, 22, colour=TEXT, size=13, bold=True)
        _lbl(w, "Exported files are NOT encrypted. Store them securely.", 20, 48, 700, 18, colour=WARN, size=11)

        btn_exp_json = _btn(w, "📋 Export JSON", 20, 78, 160, 44)
        btn_exp_csv  = _btn(w, "📊 Export CSV",  196, 78, 160, 44, style="outline")
        btn_exp_json.clicked.connect(self._export_json)
        btn_exp_csv.clicked.connect(self._export_csv)

        _lbl(w, "Import", 20, 146, 600, 22, colour=TEXT, size=13, bold=True)
        _lbl(w, "Import items from a CSV file (must match SecureVault CSV format).", 20, 174, 700, 18, colour=MUTED, size=10)
        btn_imp_csv = _btn(w, "📂 Import CSV", 20, 204, 160, 44, style="ghost")
        btn_imp_csv.clicked.connect(self._import_csv)
        self.lblDataStatus = _lbl(w, "", 20, 262, 600, 22, colour=OK, size=11)

        return w

    def _stab_folders(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        _lbl(w, "Manage Folders", 20, 20, 600, 22, colour=TEXT, size=13, bold=True)

        self.lwFolders = QListWidget(w)
        self.lwFolders.setGeometry(QRect(20, 52, 440, 220))
        self.lwFolders.setStyleSheet(f"""
            QListWidget {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; color: {TEXT}; font-size: 13px; outline: none; }}
            QListWidget::item {{ padding: 8px 14px; }}
            QListWidget::item:selected {{ background: {_rgba(ACCENT, 0.2)}; }}
        """)

        _lbl(w, "New folder name", 20, 286, 300, 22, colour=TEXT2, size=11)
        self.leNewFolder = _inp(w, 20, 310, 300, 42, "e.g. Travel")
        btn_add_folder = _btn(w, "Add",    330, 310, 80, 42)
        btn_del_folder = _btn(w, "Delete", 420, 310, 80, 42, style="danger")
        btn_add_folder.clicked.connect(self._add_folder)
        btn_del_folder.clicked.connect(self._delete_folder)

        self.lblFolderStatus = _lbl(w, "", 20, 364, 500, 22, colour=OK, size=11)
        return w

    # ── Page 5: Now Playing ──────────────────────────────────────────────

    def _page_now_playing(self) -> QWidget:
        page = QWidget()
        page.setStyleSheet(f"background: {BG};")

        _lbl(page, "Now Playing", 22, 16, 600, 32, size=18, bold=True)
        _lbl(page, "Showing media currently playing on this computer via Windows Media Session API.",
             22, 52, 900, 20, colour=MUTED, size=11)

        # Big card
        card = QFrame(page)
        card.setGeometry(QRect(22, 86, 600, 340))
        card.setStyleSheet(f"background: {CARD}; border-radius: 20px; border: 1px solid {BORDER};")

        # Album art placeholder
        art = QLabel("🎵", card)
        art.setGeometry(QRect(30, 30, 140, 140))
        art.setAlignment(Qt.AlignCenter)
        art.setFont(_f(60))
        art.setStyleSheet(f"background: {_rgba(ACCENT, 0.12)}; border-radius: 16px; color: {ACCENT};")

        self.lblNpTitle  = _lbl(card, "Nothing Playing",  190, 30,  390, 34, size=20, bold=True)
        self.lblNpArtist = _lbl(card, "",                  190, 72,  390, 24, colour=TEXT2, size=14)
        self.lblNpAlbum  = _lbl(card, "",                  190, 102, 390, 20, colour=MUTED, size=12)
        self.lblNpApp    = _lbl(card, "",                  190, 128, 390, 22, colour=INFO, size=11)

        self.lblNpStatus = QLabel("", card)
        self.lblNpStatus.setGeometry(QRect(190, 156, 140, 26))
        self.lblNpStatus.setFont(_f(11, bold=True))
        self.lblNpStatus.setAlignment(Qt.AlignCenter)
        self.lblNpStatus.setStyleSheet(f"background: {_rgba(OK, 0.2)}; color: {OK}; border-radius: 6px; border: 1px solid {_rgba(OK, 0.3)};")

        # Controls
        ctrl_y = 230
        self.btnNpPrev  = QPushButton("⏮", card)
        self.btnNpPlay  = QPushButton("⏸", card)
        self.btnNpNext  = QPushButton("⏭", card)
        for i, (btn, action) in enumerate([(self.btnNpPrev, "prev"), (self.btnNpPlay, "play_pause"), (self.btnNpNext, "next")]):
            w = 64 if i == 1 else 52
            btn.setGeometry(QRect(30 + i * 68, ctrl_y, w, w))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(_f(20))
            btn.setStyleSheet(f"""
                QPushButton {{ background: {INP}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: {w // 2}px; }}
                QPushButton:hover {{ background: {ACCENT}; border-color: {ACCENT}; }}
                QPushButton:pressed {{ background: rgb(75,75,200); }}
            """)
            act = action
            btn.clicked.connect(lambda _=False, a=act: (media_control(a), QTimer.singleShot(600, self._refresh_np_full)))

        # Refresh interval
        self.cbNpAutoRefresh = QCheckBox("Auto-refresh every 3 seconds", card)
        self.cbNpAutoRefresh.setGeometry(QRect(30, 310, 320, 28))
        self.cbNpAutoRefresh.setChecked(True)
        self.cbNpAutoRefresh.setFont(_f(12))
        self.cbNpAutoRefresh.setStyleSheet(f"color: {MUTED}; background: transparent;")

        btn_refresh = _btn(page, "Refresh Now", 640, 86, 130, 44, style="outline")
        btn_refresh.clicked.connect(self._refresh_np_full)

        self.lblNpHint = _lbl(page, "", 22, 440, 900, 22, colour=MUTED, size=11)

        return page

    # ── Status bar ────────────────────────────────────────────────────

    def _build_statusbar(self):
        self.statusBar = QFrame(self.central)
        self.statusBar.setGeometry(QRect(240, 840, 1040, 30))
        self.statusBar.setStyleSheet(f"background: {SB}; border-top: 1px solid {BORDER};")

        self.lblStatus = QLabel("", self.statusBar)
        self.lblStatus.setGeometry(QRect(16, 0, 700, 30))
        self.lblStatus.setFont(_f(10))
        self.lblStatus.setStyleSheet(f"color: {MUTED}; background: transparent;")

        self.lblClipStatus = QLabel("", self.statusBar)
        self.lblClipStatus.setGeometry(QRect(720, 0, 310, 30))
        self.lblClipStatus.setFont(_f(10))
        self.lblClipStatus.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lblClipStatus.setStyleSheet(f"color: {WARN}; background: transparent;")

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._tick_status)
        self._status_timer.start(1000)

    # ═══════════════════════════════════════════════════════════════════
    # Navigation & filtering
    # ═══════════════════════════════════════════════════════════════════

    def _nav_to(self, idx: int):
        self.stack.setCurrentIndex(idx)
        for b in self._sb_btns:
            b.setChecked(False)
        page_btn = {
            0: self.btnAll, 2: self.btnDashboard,
            3: self.btnGenerator, 4: self.btnSettings, 5: self.btnNowPlaying,
        }
        if idx in page_btn:
            page_btn[idx].setChecked(True)
        if idx == 0:
            self._refresh_list()
        elif idx == 2:
            self._refresh_dashboard()
        elif idx == 4:
            self._refresh_settings_ui()
        elif idx == 5:
            self._refresh_np_full()
        self._update_status_bar()

    def _set_filter(self, type_f: str, folder: str, favs: bool, recent: bool):
        self._filter_type   = type_f
        self._filter_folder = folder
        self._show_favs     = favs
        self._show_recent   = recent
        self.leSearch.clear()
        self._nav_to(0)
        for b in self._sb_btns:
            b.setChecked(False)
        {
            (False, False, "all",      ""):         self.btnAll,
            (True,  False, "all",      ""):         self.btnFavs,
            (False, True,  "all",      ""):         self.btnRecent,
            (False, False, "login",    ""):         self.btnLogin,
            (False, False, "note",     ""):         self.btnNote,
            (False, False, "card",     ""):         self.btnCard,
            (False, False, "identity", ""):         self.btnIdentity,
        }.get((favs, recent, type_f, folder), self.btnAll).setChecked(True)

    def _on_search(self, text: str):
        if self.stack.currentIndex() == 0:
            self._refresh_list(text)

    def _on_sort_changed(self, _):
        self._current_sort = SORT_OPTIONS[self.cmbSort.currentIndex()][0]
        if self.stack.currentIndex() == 0:
            self._refresh_list(self.leSearch.text())

    def _sort_items(self, items: list[dict]) -> list[dict]:
        key = self._current_sort
        if key == "name_asc":
            return sorted(items, key=lambda i: i.get("item_name", "").lower())
        if key == "name_desc":
            return sorted(items, key=lambda i: i.get("item_name", "").lower(), reverse=True)
        if key == "date_asc":
            return sorted(items, key=lambda i: i.get("created", ""))
        if key == "date_desc":
            return sorted(items, key=lambda i: i.get("created", ""), reverse=True)
        if key == "type":
            order = ["login", "note", "card", "identity"]
            return sorted(items, key=lambda i: order.index(i.get("item_type", "login")) if i.get("item_type") in order else 99)
        return items

    # ═══════════════════════════════════════════════════════════════════
    # List rendering
    # ═══════════════════════════════════════════════════════════════════

    def _refresh_list(self, search_query: str = ""):
        # Clear existing cards
        while self._items_layout.count():
            child = self._items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if search_query:
            items = self.storage.search(search_query)
        elif self._show_recent:
            items = self.storage.recently_added(7)
        elif self._show_favs:
            items = self.storage.favourites()
        elif self._filter_type != "all":
            items = self.storage.by_type(self._filter_type)
        elif self._filter_folder:
            items = self.storage.by_folder(self._filter_folder)
        else:
            items = self.storage.all_items()

        items = self._sort_items(items)

        title_map = {
            "all": "All Items", "login": "Logins", "note": "Secure Notes",
            "card": "Cards", "identity": "Identities",
        }
        count = len(items)
        if self._show_favs:
            self.lblListTitle.setText(f"Favourites  ({count})")
        elif self._show_recent:
            self.lblListTitle.setText(f"Recently Added  ({count})")
        elif search_query:
            self.lblListTitle.setText(f'Search: "{search_query}"  ({count})')
        else:
            self.lblListTitle.setText(f"{title_map.get(self._filter_type, 'Items')}  ({count})")

        if not items:
            empty = QLabel("No items found.")
            empty.setFont(_f(13))
            empty.setStyleSheet(f"color: {MUTED}; background: transparent;")
            empty.setAlignment(Qt.AlignCenter)
            self._items_layout.addWidget(empty)
        else:
            for item in items:
                card = ItemCard(
                    item,
                    copy_pw_fn=lambda v: self._copy_to_clipboard(v, "Password"),
                    copy_user_fn=lambda v: self._copy_to_clipboard(v, "Username"),
                    parent=self._items_widget,
                )
                card.opened.connect(self._open_item_by_id)
                card.menu.connect(self._list_context_menu)
                self._items_layout.addWidget(card)

        self._items_layout.addStretch()

    def _list_context_menu(self, item_id: str, pos: QPoint):
        item = self.storage.get_by_id(item_id)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {CARD}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}
            QMenu::item {{ padding: 8px 20px; border-radius: 6px; }}
            QMenu::item:selected {{ background: {_rgba(ACCENT, 0.2)}; }}
        """)

        act_cp_pw = act_cp_us = act_url = None
        if item.get("item_type") == "login":
            act_cp_pw = menu.addAction("🔑  Copy Password")
            act_cp_us = menu.addAction("👤  Copy Username")
            if item.get("website"):
                act_url = menu.addAction("🌐  Open Website")
            menu.addSeparator()

        act_open = menu.addAction("✏️  Open / Edit")
        act_dup  = menu.addAction("⎘  Duplicate")
        act_fav  = menu.addAction("★  " + ("Remove from Favourites" if item.get("favourite") else "Add to Favourites"))
        menu.addSeparator()
        act_del  = menu.addAction("🗑  Delete")

        chosen = menu.exec(pos)
        if not chosen:
            return

        if chosen == act_cp_pw:
            self._copy_to_clipboard(item.get("password", ""), "Password")
        elif chosen == act_cp_us:
            self._copy_to_clipboard(item.get("username", ""), "Username")
        elif chosen == act_url:
            import webbrowser
            webbrowser.open(item.get("website", ""))
        elif chosen == act_open:
            self._open_item_by_id(item_id)
        elif chosen == act_dup:
            new = self.storage.duplicate_item(item_id)
            if new:
                self._refresh_list(self.leSearch.text())
        elif chosen == act_fav:
            self.storage.toggle_favourite(item_id)
            self._refresh_list(self.leSearch.text())
        elif chosen == act_del:
            self._confirm_delete(item_id)

    # ═══════════════════════════════════════════════════════════════════
    # Edit / Add item
    # ═══════════════════════════════════════════════════════════════════

    def _new_item(self):
        self._current_id = None
        self._clear_form()
        self.lblEditTitle.setText("Add Item")
        self.btnDelete.setVisible(False)
        self.btnDuplicate.setVisible(False)
        self.btnHistPw.setVisible(False)
        self._populate_folder_combo()
        # Set default item type from settings
        type_keys = list(ITEM_TYPES.keys())
        default_type = self.storage.get_settings().get("default_item_type", "login")
        if default_type in type_keys:
            self.cmbType.setCurrentIndex(type_keys.index(default_type))
        self._nav_to(1)

    def _open_item_by_id(self, item_id: str):
        item = self.storage.get_by_id(item_id)
        if not item:
            return
        self._current_id = item_id
        self.lblEditTitle.setText("Edit Item")
        self.btnDelete.setVisible(True)
        self.btnDuplicate.setVisible(True)
        self.btnHistPw.setVisible(bool(item.get("password_history")))
        self._populate_folder_combo()
        self._load_form(item)
        self._nav_to(1)

    def _clear_form(self):
        for w in [self.leItemName, self.leUsername, self.lePassword, self.leWebsite,
                  self.leTotp, self.leTags, self.leCardHolder, self.leCardNumber,
                  self.leCardBrand, self.leCardExpiry, self.leCardCvv,
                  self.leFirstName, self.leLastName, self.leEmail, self.lePhone, self.leAddress]:
            w.clear()
        self.teNotes.clear()
        self.cbFavourite.setChecked(False)
        self.cmbType.setCurrentIndex(0)
        self.lblEditStatus.setText("")
        self._pw_visible = False
        self.lePassword.setEchoMode(QLineEdit.Password)
        self.btnTogglePw.setText("Show")
        self.pbStrength.setValue(0)
        self.lblStrength.setText("")

    def _load_form(self, item: dict):
        self._clear_form()
        type_keys = list(ITEM_TYPES.keys())
        try:
            self.cmbType.setCurrentIndex(type_keys.index(item.get("item_type", "login")))
        except ValueError:
            self.cmbType.setCurrentIndex(0)

        self.leItemName.setText(item.get("item_name", ""))
        self.leUsername.setText(item.get("username", ""))
        self.lePassword.setText(item.get("password", ""))
        self.leWebsite.setText(item.get("website", ""))
        self.leTotp.setText(item.get("totp_secret", ""))
        self.teNotes.setPlainText(item.get("notes", ""))
        self.leTags.setText(", ".join(item.get("tags", [])))
        self.cbFavourite.setChecked(item.get("favourite", False))

        folder = item.get("folder", "")
        idx = self.cmbFolder.findText(folder)
        if idx >= 0:
            self.cmbFolder.setCurrentIndex(idx)

        self.leCardHolder.setText(item.get("card_holder", ""))
        self.leCardNumber.setText(item.get("card_number", ""))
        self.leCardBrand.setText(item.get("card_brand", ""))
        self.leCardExpiry.setText(item.get("card_expiry_date", ""))
        self.leCardCvv.setText(item.get("card_cvv", ""))
        self.leFirstName.setText(item.get("first_name", ""))
        self.leLastName.setText(item.get("last_name", ""))
        self.leEmail.setText(item.get("email", ""))
        self.lePhone.setText(item.get("phone", ""))
        self.leAddress.setText(item.get("address", ""))

        if item.get("password"):
            self._update_strength(item["password"])

    def _populate_folder_combo(self):
        self.cmbFolder.clear()
        self.cmbFolder.addItem("(None)")
        for f in self.storage.get_folders():
            self.cmbFolder.addItem(f)

    def _on_type_changed(self, idx: int):
        type_keys = list(ITEM_TYPES.keys())
        t = type_keys[idx] if idx < len(type_keys) else "login"
        self.frameLogin.setVisible(t == "login")
        self.frameCard.setVisible(t == "card")
        self.frameIdentity.setVisible(t == "identity")

    def _toggle_pw_visible(self):
        self._pw_visible = not self._pw_visible
        self.lePassword.setEchoMode(QLineEdit.Normal if self._pw_visible else QLineEdit.Password)
        self.btnTogglePw.setText("Hide" if self._pw_visible else "Show")

    def _update_strength(self, text: str):
        r = PasswordStrength.analyse(text)
        self.pbStrength.setValue(r["score"])
        self.pbStrength.setStyleSheet(f"QProgressBar {{ background: {BORDER}; border-radius: 3px; }} QProgressBar::chunk {{ background: {r['colour']}; border-radius: 3px; }}")
        self.lblStrength.setText(f"{r['level']}  ·  {r['feedback'][0]}  ·  Entropy: {r['entropy']} bits")
        self.lblStrength.setStyleSheet(f"color: {r['colour']}; background: transparent; font-size: 11px;")

    def _quick_generate(self):
        s = self.storage.get_settings()
        pw = self.generator.generate_password(
            length=s.get("default_generator_length", 20),
            include_letters=s.get("default_generator_letters", True),
            include_numbers=s.get("default_generator_numbers", True),
            include_special=s.get("default_generator_special", True),
            exclude_ambiguous=s.get("default_generator_exclude_ambiguous", False),
        )
        self.lePassword.setText(pw)

    def _show_pw_history(self):
        if not self._current_id:
            return
        item = self.storage.get_by_id(self._current_id)
        history = item.get("password_history", []) if item else []
        dlg = PasswordHistoryDialog(history, self)
        dlg.exec()

    def _save_item(self):
        name = self.leItemName.text().strip()
        if not name:
            self.lblEditStatus.setText("Item name is required.")
            self.lblEditStatus.setStyleSheet(f"color: {ERR}; background: transparent; font-size: 11px;")
            return

        type_keys = list(ITEM_TYPES.keys())
        folder = self.cmbFolder.currentText()
        if folder == "(None)":
            folder = ""

        d = {
            "item_name":        name,
            "item_type":        type_keys[self.cmbType.currentIndex()],
            "folder":           folder,
            "favourite":        self.cbFavourite.isChecked(),
            "notes":            self.teNotes.toPlainText(),
            "tags":             [t.strip() for t in self.leTags.text().split(",") if t.strip()],
            "username":         self.leUsername.text(),
            "password":         self.lePassword.text(),
            "website":          self.leWebsite.text(),
            "totp_secret":      self.leTotp.text(),
            "card_holder":      self.leCardHolder.text(),
            "card_number":      self.leCardNumber.text(),
            "card_brand":       self.leCardBrand.text(),
            "card_expiry_date": self.leCardExpiry.text(),
            "card_cvv":         self.leCardCvv.text(),
            "first_name":       self.leFirstName.text(),
            "last_name":        self.leLastName.text(),
            "email":            self.leEmail.text(),
            "phone":            self.lePhone.text(),
            "address":          self.leAddress.text(),
        }

        if self._current_id:
            self.storage.update_item(self._current_id, d)
            msg = "Item updated."
        else:
            self.storage.add_item(d)
            msg = "Item saved."

        self.lblEditStatus.setText(msg)
        self.lblEditStatus.setStyleSheet(f"color: {OK}; background: transparent; font-size: 11px;")
        self._refresh_list()
        self._update_status_bar()

    def _duplicate_item(self):
        if not self._current_id:
            return
        new = self.storage.duplicate_item(self._current_id)
        if new:
            self._current_id = new["id"]
            self._load_form(new)
            self.lblEditTitle.setText("Edit Item (Copy)")
            self.lblEditStatus.setText("Duplicated. Edit and save as a new item.")
            self.lblEditStatus.setStyleSheet(f"color: {INFO}; background: transparent; font-size: 11px;")
            self._refresh_list()

    def _delete_item(self):
        if not self._current_id:
            return
        self._confirm_delete(self._current_id, go_back=True)

    def _confirm_delete(self, item_id: str, go_back: bool = False):
        settings = self.storage.get_settings()
        if settings.get("confirm_delete", True):
            reply = QMessageBox.question(
                self, "Delete Item",
                "Are you sure you want to delete this item?\nThis cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.storage.delete_item(item_id)
        if self._current_id == item_id:
            self._current_id = None
        if go_back:
            self._back_to_list()
        else:
            self._refresh_list(self.leSearch.text())

    def _back_to_list(self):
        self._nav_to(0)

    # ═══════════════════════════════════════════════════════════════════
    # Dashboard
    # ═══════════════════════════════════════════════════════════════════

    def _refresh_dashboard(self):
        counts = self.storage.count_by_type()
        total  = len(self.storage.all_items())
        health = self.storage.vault_health()

        self.lblDTotal.setText(str(total))
        self.lblDLogins.setText(str(counts.get("login", 0)))
        self.lblDNotes.setText(str(counts.get("note", 0)))
        self.lblDCards.setText(str(counts.get("card", 0)))
        score_val = health["overall_score"]
        self.lblDScore.setText(f"{score_val}%")
        self.pbScore.setValue(score_val)

        self.lwWeak.clear()
        for w in health["weak"]:
            self.lwWeak.addItem(f"  {w['name']}  —  score {w['score']}/100")

        self.lwReused.clear()
        seen: set = set()
        for r in health["reused"]:
            entry = f"  {r['name']}"
            if entry not in seen:
                seen.add(entry)
                self.lwReused.addItem(entry)

        self.lwOld.clear()
        for o in health["old"]:
            self.lwOld.addItem(f"  {o['name']}")

    # ═══════════════════════════════════════════════════════════════════
    # Generator
    # ═══════════════════════════════════════════════════════════════════

    def _on_gen_mode_changed(self, idx: int):
        self.fGenPw.setVisible(idx == 0)
        self.fGenPhrase.setVisible(idx == 1)
        self._run_generator()

    def _run_generator(self):
        mode = self.cmbGenMode.currentIndex()
        if mode == 0:
            pw = self.generator.generate_password(
                length=self.sbGenLen.value(),
                include_letters=self.cbGenLetters.isChecked(),
                include_numbers=self.cbGenNumbers.isChecked(),
                include_special=self.cbGenSpecial.isChecked(),
                exclude_ambiguous=self.cbGenAmbig.isChecked(),
            )
        elif mode == 1:
            sep = self.lePhrSep.text() or "-"
            pw = self.generator.generate_passphrase(
                word_count=self.sbGenWords.value(),
                separator=sep,
                capitalise=self.cbPhrCap.isChecked(),
                add_number=self.cbPhrNum.isChecked(),
            )
        else:
            pw = self.generator.generate_username()

        self.leGenOut.setText(pw)

        r = PasswordStrength.analyse(pw)
        self.pbGenStr.setValue(r["score"])
        self.pbGenStr.setStyleSheet(f"QProgressBar {{ background: {BORDER}; border-radius: 3px; }} QProgressBar::chunk {{ background: {r['colour']}; border-radius: 3px; }}")
        self.lblGenStr.setText(f"{r['level']}  ·  Entropy: {r['entropy']} bits  ·  {r['feedback'][0]}")
        self.lblGenStr.setStyleSheet(f"color: {r['colour']}; background: transparent; font-size: 11px;")
        self.lblGenEntropy.setText(f"{r['entropy']} bits")

    def _copy_generated(self):
        pw = self.leGenOut.text()
        if pw:
            now = datetime.now().strftime("%H:%M:%S")
            self._gen_history.insert(0, f"{pw}  →  {now}")
            if len(self._gen_history) > 20:
                self._gen_history = self._gen_history[:20]
            self._refresh_gen_history()
            self._copy_to_clipboard(pw, "Generated password")

    def _refresh_gen_history(self):
        self.lwGenHistory.clear()
        for entry in self._gen_history:
            self.lwGenHistory.addItem(entry)

    # ═══════════════════════════════════════════════════════════════════
    # Settings
    # ═══════════════════════════════════════════════════════════════════

    def _refresh_settings_ui(self):
        s = self.storage.get_settings()
        self.sbAutoLock.setValue(s.get("auto_lock_minutes", 5))
        self.sbClipClear.setValue(s.get("clipboard_clear_seconds", 30))
        self.cbConfirmDelete.setChecked(s.get("confirm_delete", True))

        sort_keys = [k for k, _ in SORT_OPTIONS]
        sort_key  = s.get("default_sort", "name_asc")
        if sort_key in sort_keys:
            self.cmbDefaultSort.setCurrentIndex(sort_keys.index(sort_key))

        density = s.get("list_density", "comfortable")
        self.cmbDensity.setCurrentIndex(0 if density == "comfortable" else 1)

        type_keys = list(ITEM_TYPES.keys())
        def_type  = s.get("default_item_type", "login")
        if def_type in type_keys:
            self.cmbDefaultType.setCurrentIndex(type_keys.index(def_type))

        self.sbDefLen.setValue(s.get("default_generator_length", 20))
        self.cbDefLetters.setChecked(s.get("default_generator_letters", True))
        self.cbDefNumbers.setChecked(s.get("default_generator_numbers", True))
        self.cbDefSpecial.setChecked(s.get("default_generator_special", True))
        self.cbDefAmbig.setChecked(s.get("default_generator_exclude_ambiguous", False))
        self.sbDefWords.setValue(s.get("default_generator_passphrase_words", 4))
        self.leDefSep.setText(s.get("default_generator_passphrase_sep", "-"))

        accent = s.get("accent_color", "indigo")
        for btn in self._accent_btns:
            btn.setChecked(btn.text().lower() == accent.lower())

        self.lwFolders.clear()
        for f in self.storage.get_folders():
            self.lwFolders.addItem(f)

    def _save_settings(self):
        sort_keys   = [k for k, _ in SORT_OPTIONS]
        type_keys   = list(ITEM_TYPES.keys())
        density_map = {0: "comfortable", 1: "compact"}

        updates = {
            "auto_lock_minutes":                      self.sbAutoLock.value(),
            "clipboard_clear_seconds":                self.sbClipClear.value(),
            "confirm_delete":                         self.cbConfirmDelete.isChecked(),
            "default_sort":                           sort_keys[self.cmbDefaultSort.currentIndex()],
            "list_density":                           density_map[self.cmbDensity.currentIndex()],
            "default_item_type":                      type_keys[self.cmbDefaultType.currentIndex()],
            "default_generator_length":               self.sbDefLen.value(),
            "default_generator_letters":              self.cbDefLetters.isChecked(),
            "default_generator_numbers":              self.cbDefNumbers.isChecked(),
            "default_generator_special":              self.cbDefSpecial.isChecked(),
            "default_generator_exclude_ambiguous":    self.cbDefAmbig.isChecked(),
            "default_generator_passphrase_words":     self.sbDefWords.value(),
            "default_generator_passphrase_sep":       self.leDefSep.text() or "-",
        }
        # Accent
        for btn in self._accent_btns:
            if btn.isChecked():
                updates["accent_color"] = btn.text().lower()

        self.storage.update_settings(updates)
        self._current_sort = updates["default_sort"]
        self._apply_settings()

        for lbl in [self.lblSecStatus, self.lblVaultStatus, self.lblGenStatus, self.lblAppStatus]:
            lbl.setText("Saved.")
            QTimer.singleShot(3000, lambda l=lbl: l.setText(""))

    def _apply_settings(self):
        s = self.storage.get_settings()
        mins = s.get("auto_lock_minutes", 5)
        self._lock_timer.stop()
        if mins > 0:
            self._lock_timer.start(mins * 60 * 1000)
        self._clip_secs = s.get("clipboard_clear_seconds", 30)
        sort_key = s.get("default_sort", "name_asc")
        sort_keys = [k for k, _ in SORT_OPTIONS]
        if sort_key in sort_keys:
            self.cmbSort.setCurrentIndex(sort_keys.index(sort_key))
            self._current_sort = sort_key

    def _set_accent(self, key: str):
        for btn in self._accent_btns:
            btn.setChecked(btn.text().lower() == key.lower())

    def _add_folder(self):
        name = self.leNewFolder.text().strip()
        if self.storage.add_folder(name):
            self.leNewFolder.clear()
            self._refresh_settings_ui()
            self.lblFolderStatus.setText(f"Folder '{name}' added.")
            QTimer.singleShot(3000, lambda: self.lblFolderStatus.setText(""))
        else:
            self.lblFolderStatus.setText("Folder name empty or already exists.")
            self.lblFolderStatus.setStyleSheet(f"color: {ERR}; background: transparent; font-size: 11px;")

    def _delete_folder(self):
        item = self.lwFolders.currentItem()
        if not item:
            return
        reply = QMessageBox.question(
            self, "Delete Folder",
            f'Delete folder "{item.text()}"?\nItems inside will become unassigned.',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.storage.delete_folder(item.text())
            self._refresh_settings_ui()

    # ═══════════════════════════════════════════════════════════════════
    # Now Playing
    # ═══════════════════════════════════════════════════════════════════

    def _refresh_np_mini(self):
        info = get_media_info()
        if info:
            title = info["title"][:28] + ("…" if len(info["title"]) > 28 else "")
            artist_app = f"{info['artist']}  ·  {info['app']}" if info["artist"] else info["app"]
            self.npTitle.setText(title or "Now Playing")
            self.npArtist.setText(artist_app[:34])
            self.npApp.setText("● " + info["status"])
        else:
            self.npTitle.setText("Nothing playing")
            self.npArtist.setText("")
            self.npApp.setText("")

    def _refresh_np_full(self):
        self._refresh_np_mini()
        info = get_media_info()
        if info:
            self.lblNpTitle.setText(info["title"] or "Unknown Title")
            self.lblNpArtist.setText(info["artist"] or "Unknown Artist")
            self.lblNpAlbum.setText(info["album"] or "")
            self.lblNpApp.setText(f"Playing via  {info['app']}")
            is_playing = info["status"] == "Playing"
            self.lblNpStatus.setText(f"  {'▶ Playing' if is_playing else '⏸ Paused'}  ")
            status_col = OK if is_playing else WARN
            self.lblNpStatus.setStyleSheet(f"background: {_rgba(status_col, 0.2)}; color: {status_col}; border-radius: 6px; border: 1px solid {_rgba(status_col, 0.3)};")
            self.btnNpPlay.setText("⏸" if is_playing else "▶")
            self.lblNpHint.setText(f"Source app ID:  {info.get('app', '')}  ·  Double-click history entries to copy.")
        else:
            self.lblNpTitle.setText("Nothing Playing")
            self.lblNpArtist.setText("")
            self.lblNpAlbum.setText("")
            self.lblNpApp.setText("")
            self.lblNpStatus.setText("  No session  ")
            self.lblNpStatus.setStyleSheet(f"background: {_rgba(MUTED, 0.2)}; color: {MUTED}; border-radius: 6px;")
            self.lblNpHint.setText("No media session found. Start playing music in Spotify, Chrome, VLC, etc.")

    # ═══════════════════════════════════════════════════════════════════
    # Clipboard
    # ═══════════════════════════════════════════════════════════════════

    def _copy_to_clipboard(self, text: str, what: str = ""):
        if not text:
            return
        QApplication.clipboard().setText(text)
        self._clipboard_val = text
        secs = self._clip_secs
        if secs > 0:
            self._clip_timer.start(secs * 1000)
            self._clip_remaining = secs
        self._update_status_bar(f"✓ {what} copied")

    def _clear_clipboard(self):
        if QApplication.clipboard().text() == self._clipboard_val:
            QApplication.clipboard().clear()
        self._clipboard_val = ""
        self._clip_remaining = 0
        self._update_status_bar()

    # ═══════════════════════════════════════════════════════════════════
    # Status bar
    # ═══════════════════════════════════════════════════════════════════

    def _update_status_bar(self, flash: str = ""):
        counts = self.storage.count_by_type()
        total  = sum(counts.values())
        self.lblStatus.setText(
            f"  🔐 {self.username}  ·  {total} items  ·  "
            f"{counts.get('login',0)} logins  ·  {counts.get('note',0)} notes"
            + (f"  ·  {flash}" if flash else "")
        )

    def _tick_status(self):
        if self._clip_timer.isActive():
            remaining = self._clip_timer.remainingTime() // 1000
            self.lblClipStatus.setText(f"📋 Clearing clipboard in {remaining}s")
        else:
            self.lblClipStatus.setText("")

    # ═══════════════════════════════════════════════════════════════════
    # Import / Export
    # ═══════════════════════════════════════════════════════════════════

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Vault (JSON)", "vault_export.json", "JSON Files (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.storage.export_json())
            self.lblDataStatus.setText(f"Exported to {os.path.basename(path)}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Vault (CSV)", "vault_export.csv", "CSV Files (*.csv)")
        if path:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(self.storage.export_csv())
            self.lblDataStatus.setText(f"Exported to {os.path.basename(path)}")

    def _import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, "r", encoding="utf-8") as f:
                count = self.storage.import_csv(f.read())
            self.lblDataStatus.setText(f"Imported {count} items.")
            self._refresh_list()

    # ═══════════════════════════════════════════════════════════════════
    # Update checker
    # ═══════════════════════════════════════════════════════════════════

    def _start_update_check(self):
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()

    def _on_update_available(self, new_version: str):
        import webbrowser
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"<b>SecureVault {new_version} is available.</b>")
        msg.setInformativeText(
            f"You are running version {APP_VERSION}.\n"
            "Download the latest installer from GitHub?"
        )
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.button(QMessageBox.Ok).setText("Download Update")
        msg.button(QMessageBox.Cancel).setText("Not Now")
        msg.setDefaultButton(QMessageBox.Ok)
        if msg.exec() == QMessageBox.Ok:
            webbrowser.open(
                "https://github.com/edgegithuber7/Secure_vault/releases/latest"
            )

    # ═══════════════════════════════════════════════════════════════════
    # Auto-lock
    # ═══════════════════════════════════════════════════════════════════

    def _auto_lock(self):
        self._lock_timer.stop()
        self._lock_vault()

    def _lock_vault(self):
        self._np_timer.stop()
        from login import LoginWindow
        self.login_win = LoginWindow()
        self.login_win.show()
        self.close()


# ── Entry point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    from login import LoginWindow
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())
