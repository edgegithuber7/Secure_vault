"""
login.py – Login and registration window for SecureVault.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QMessageBox, QFrame,
)

from Authentication import check_cridentials, register_user

DARK_BG = "rgb(15,18,40)"
PANEL_BG = "rgb(26,30,55)"
ACCENT = "rgb(46,94,244)"
TEXT = "rgb(220,224,255)"
MUTED = "rgb(130,140,180)"
ERROR = "rgb(239,68,68)"
SUCCESS = "rgb(34,197,94)"
INPUT_BG = "rgb(36,42,72)"
BORDER = "rgb(60,70,110)"


def _label(parent: QWidget, text: str, x: int, y: int, w: int, h: int,
           colour: str = TEXT, size: int = 13, bold: bool = False) -> QLabel:
    lbl = QLabel(text, parent)
    lbl.setGeometry(QRect(x, y, w, h))
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    lbl.setFont(font)
    lbl.setStyleSheet(f"color: {colour}; background: transparent;")
    return lbl


def _input(parent: QWidget, x: int, y: int, w: int, h: int,
           placeholder: str = "", password: bool = False) -> QLineEdit:
    le = QLineEdit(parent)
    le.setGeometry(QRect(x, y, w, h))
    le.setPlaceholderText(placeholder)
    if password:
        le.setEchoMode(QLineEdit.Password)
    le.setStyleSheet(f"""
        QLineEdit {{
            background: {INPUT_BG};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 0 10px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {ACCENT};
        }}
    """)
    return le


def _button(parent: QWidget, text: str, x: int, y: int, w: int, h: int,
            primary: bool = True) -> QPushButton:
    btn = QPushButton(text, parent)
    btn.setGeometry(QRect(x, y, w, h))
    btn.setCursor(Qt.PointingHandCursor)
    if primary:
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: rgb(66,114,255); }}
            QPushButton:pressed {{ background: rgb(30,70,200); }}
        """)
    else:
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: rgba(46,94,244,0.15); }}
        """)
    return btn


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecureVault")
        self.setFixedSize(460, 560)
        self.setStyleSheet(f"background: {DARK_BG};")

        self.central = QWidget(self)
        self.setCentralWidget(self.central)

        self.stack = QStackedWidget(self.central)
        self.stack.setGeometry(QRect(0, 0, 460, 560))

        self._build_login_page()
        self._build_register_page()
        self.stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Login page (index 0)
    # ------------------------------------------------------------------

    def _build_login_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {DARK_BG};")

        # Panel
        panel = QFrame(page)
        panel.setGeometry(QRect(40, 60, 380, 440))
        panel.setStyleSheet(f"""
            QFrame {{
                background: {PANEL_BG};
                border-radius: 16px;
            }}
        """)

        _label(panel, "SecureVault", 0, 30, 380, 50,
               colour=TEXT, size=26, bold=True).setAlignment(Qt.AlignCenter)
        _label(panel, "Sign in to your vault", 0, 82, 380, 24,
               colour=MUTED, size=12).setAlignment(Qt.AlignCenter)

        _label(panel, "Username", 30, 130, 320, 22)
        self.leUsername_login = _input(panel, 30, 156, 320, 44, "Enter username")

        _label(panel, "Password", 30, 215, 320, 22)
        self.lePassword_login = _input(panel, 30, 241, 320, 44, "Enter password", password=True)
        self.lePassword_login.returnPressed.connect(self._handle_login)

        self.lblLoginError = _label(panel, "", 30, 295, 320, 22, colour=ERROR, size=11)
        self.lblLoginError.setWordWrap(True)

        self.btnLogin = _button(panel, "Sign In", 30, 322, 320, 46)
        self.btnLogin.clicked.connect(self._handle_login)

        _label(panel, "Don't have an account?", 30, 384, 200, 22, colour=MUTED, size=11)
        btn_reg = _button(panel, "Create Account", 235, 380, 115, 30, primary=False)
        btn_reg.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        self.stack.addWidget(page)

    # ------------------------------------------------------------------
    # Register page (index 1)
    # ------------------------------------------------------------------

    def _build_register_page(self):
        page = QWidget()
        page.setStyleSheet(f"background: {DARK_BG};")

        panel = QFrame(page)
        panel.setGeometry(QRect(40, 50, 380, 470))
        panel.setStyleSheet(f"background: {PANEL_BG}; border-radius: 16px;")

        _label(panel, "Create Account", 0, 28, 380, 44,
               colour=TEXT, size=22, bold=True).setAlignment(Qt.AlignCenter)
        _label(panel, "Set up your SecureVault", 0, 72, 380, 22,
               colour=MUTED, size=11).setAlignment(Qt.AlignCenter)

        _label(panel, "Username", 30, 110, 320, 22)
        self.leUsername_reg = _input(panel, 30, 134, 320, 44, "Choose a username")

        _label(panel, "Password", 30, 192, 320, 22)
        self.lePassword_reg = _input(panel, 30, 216, 320, 44, "Choose a master password", password=True)

        _label(panel, "Confirm Password", 30, 274, 320, 22)
        self.leConfirm_reg = _input(panel, 30, 298, 320, 44, "Confirm master password", password=True)
        self.leConfirm_reg.returnPressed.connect(self._handle_register)

        self.lblRegError = _label(panel, "", 30, 350, 320, 22, colour=ERROR, size=11)
        self.lblRegSuccess = _label(panel, "", 30, 350, 320, 22, colour=SUCCESS, size=11)

        self.btnRegister = _button(panel, "Create Account", 30, 376, 320, 46)
        self.btnRegister.clicked.connect(self._handle_register)

        btn_back = _button(panel, "Back to Sign In", 30, 428, 320, 30, primary=False)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        self.stack.addWidget(page)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _handle_login(self):
        username = self.leUsername_login.text().strip()
        password = self.lePassword_login.text()
        self.lblLoginError.setText("")

        if not username or not password:
            self.lblLoginError.setText("Please enter your username and password.")
            return

        if check_cridentials(self, username, password):
            from main import SecureVault
            self.vault = SecureVault(username, password)
            self.vault.show()
            self.close()
        else:
            self.lblLoginError.setText("Invalid username or password.")
            self.lePassword_login.clear()

    def _handle_register(self):
        username = self.leUsername_reg.text().strip()
        password = self.lePassword_reg.text()
        confirm = self.leConfirm_reg.text()
        self.lblRegError.setText("")
        self.lblRegSuccess.setText("")

        if not username or not password:
            self.lblRegError.setText("Username and password are required.")
            return
        if len(password) < 8:
            self.lblRegError.setText("Password must be at least 8 characters.")
            return
        if password != confirm:
            self.lblRegError.setText("Passwords do not match.")
            return

        if register_user(username, password):
            self.lblRegSuccess.setText("Account created! You can now sign in.")
            self.leUsername_reg.clear()
            self.lePassword_reg.clear()
            self.leConfirm_reg.clear()
        else:
            self.lblRegError.setText("Username already taken.")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec())
