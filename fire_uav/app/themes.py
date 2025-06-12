# ───────────────── minimal Steam-style QSS ────────────────── #
STYLE_STEAM_DARK = """
QWidget        { background:#1b1d22; color:#d0d2d6; font:10pt "Segoe UI"; }
QTabBar::tab   { background:#2a2d32; margin-top:6px; padding:6px 18px;
                 border-top-left-radius:4px; border-top-right-radius:4px; }
QTabBar::tab:selected{ background:#3e4249; }
QPushButton    { background:#2d89ef; color:#fff; padding:8px 24px;
                 border:none; border-radius:6px; font-weight:600; }
QPushButton:hover   { background:#3c96ff; }
QPushButton:pressed { background:#237ae0; }
QPushButton:disabled{ background:#44474e; color:#9a9ca0; }
QSlider::groove:horizontal { background:#3a3d42; height:4px; border-radius:2px; }
QSlider::handle:horizontal { background:#6ea8ff; width:14px; margin:-5px 0;
                             border-radius:7px; }
QTextEdit,QPlainTextEdit { background:#282b30; border:1px solid #3a3d42; }
QLabel#toast { background:#3e4249; color:#d0d2d6; padding:8px 20px;
               border-radius:6px; }
"""

STYLE_STEAM_LIGHT = """
QWidget        { background:#f1f3f6; color:#202225; font:10pt "Segoe UI"; }
QTabBar::tab   { background:#e4e6ea; margin-top:6px; padding:6px 18px;
                 border-top-left-radius:4px; border-top-right-radius:4px; }
QTabBar::tab:selected{ background:#ffffff; }
QPushButton    { background:#2d89ef; color:#fff; padding:8px 24px;
                 border:none; border-radius:6px; font-weight:600; }
QPushButton:hover   { background:#3c96ff; }
QPushButton:pressed { background:#237ae0; }
QPushButton:disabled{ background:#adb1b8; color:#62666c; }
QSlider::groove:horizontal { background:#c9ccd1; height:4px; border-radius:2px; }
QSlider::handle:horizontal { background:#2d89ef; width:14px; margin:-5px 0;
                             border-radius:7px; }
QTextEdit,QPlainTextEdit { background:#ffffff; border:1px solid #c9ccd1; }
QLabel#toast { background:#3e4249; color:#ffffff; padding:8px 20px;
               border-radius:6px; }
"""
