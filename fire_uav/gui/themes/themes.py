STYLE_STEAM_DARK = """ # noqa: E501
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

STYLE_STEAM_LIGHT = """ # noqa: E501
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

STYLE_LIQUID_GLASS = """ # noqa: E501
* { font-family:"Inter","Segoe UI"; font-size:10pt; }
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0   #05070d,
        stop:0.6 #0a111b,
        stop:1   #04060c);
    color:#f6fbff;
}
QWidget {
    background:transparent;
    color:#f6fbff;
}
QWidget#appRoot {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0   #070c15,
        stop:0.6 #0b1320,
        stop:1   #05070d);
}
QMenuBar {
    background:rgba(255,255,255,0.02);
    border-bottom:1px solid rgba(255,255,255,0.12);
}
QMenuBar::item { padding:6px 16px; }
QMenuBar::item:selected { background:rgba(255,255,255,0.08); border-radius:6px; }
QMenu {
    background:#101621;
    border:1px solid rgba(255,255,255,0.18);
}
QTabWidget::pane {
    border:none;
    background:transparent;
}
QTabBar::tab {
    background:rgba(255,255,255,0.08);
    padding:10px 26px;
    margin:0 6px;
    border-radius:18px;
    color:#d5e7ff;
}
QTabBar::tab:selected {
    background:rgba(255,255,255,0.22);
    color:#0a131f;
    font-weight:600;
}
QGroupBox, QWidget#panelCard, QWidget#planWidgetRoot, QWidget#videoPane {
    border-radius:24px;
    border:1px solid rgba(255,255,255,0.18);
    background:rgba(255,255,255,0.08);
    padding:18px;
}
QWidget#planWidgetRoot QPushButton,
QWidget#panelCard QPushButton {
    min-height:34px;
}
QWidget#planWidgetRoot {
    padding:8px;
}
QWidget#videoPane {
    padding:0;
}
QScrollArea {
    border:none;
}
QScrollBar:vertical {
    width:10px;
    background:transparent;
}
QScrollBar::handle:vertical {
    background:rgba(255,255,255,0.2);
    border-radius:5px;
}
QPushButton {
    border:none;
    border-radius:16px;
    padding:10px 28px;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0   #fbfbff,
        stop:1   #cfe0ff);
    color:#0c111a;
    font-weight:600;
}
QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0   #ffffff,
        stop:1   #dfe9ff);
}
QPushButton:pressed {
    background:rgba(240,240,255,0.85);
}
QPushButton#plannerBtn {
    padding:8px 20px;
    border-radius:14px;
}
QTextEdit,QPlainTextEdit {
    background:rgba(6,10,18,0.85);
    border:1px solid rgba(255,255,255,0.13);
    border-radius:18px;
    padding:12px;
    color:#dfe9ff;
}
QSlider::groove:horizontal {
    background:rgba(255,255,255,0.18);
    height:6px;
    border-radius:6px;
}
QSlider::handle:horizontal {
    background:#8ed0ff;
    width:18px;
    margin:-6px 0;
    border-radius:9px;
    border:2px solid rgba(255,255,255,0.9);
}
QLabel#toast {
    background:rgba(0,0,0,0.6);
    color:#fdfdff;
    padding:10px 22px;
    border-radius:20px;
}
"""
