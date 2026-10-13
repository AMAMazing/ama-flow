STYLESHEET = """
QMainWindow {
    background-color: #0c0c0e;
}
QWidget#central {
    background-color: #0c0c0e;
}

/* Apple-inspired frosted cards */
QFrame#card {
    background-color: #161619;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
}
QFrame#card:hover {
    border: 1px solid rgba(255, 255, 255, 0.12);
}

QFrame#status_card {
    background-color: #131316;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
}

/* Typography */
QLabel {
    color: #e5e5ea;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI Variable Text", "SF Pro Display", "Segoe UI", sans-serif;
    font-size: 13px;
}
QLabel#app_title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.4px;
}
QLabel#app_subtitle {
    font-size: 12px;
    color: #8e8e93;
}
QLabel#section_heading {
    font-size: 11px;
    font-weight: 700;
    color: #8e8e93;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}
QLabel#card_title {
    font-size: 14px;
    font-weight: 600;
    color: #f2f2f7;
}
QLabel#card_subtitle {
    font-size: 12px;
    color: #8e8e93;
}

/* Segmented Buttons / Pill Selectors */
QPushButton.segment_btn {
    background-color: #1c1c1e;
    color: #8e8e93;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton.segment_btn:hover {
    background-color: #242428;
    color: #f2f2f7;
}
QPushButton.segment_btn:checked {
    background-color: #2c2c30;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.15);
}

/* Primary Action Buttons */
QPushButton#primary_action {
    background-color: #0a84ff;
    color: #ffffff;
    font-weight: 600;
    font-size: 13px;
    border: none;
    border-radius: 10px;
    padding: 8px 18px;
}
QPushButton#primary_action:hover {
    background-color: #0071e3;
}
QPushButton#primary_action:pressed {
    background-color: #0062c4;
}

/* Secondary Action Buttons */
QPushButton#secondary_action {
    background-color: #1c1c1e;
    color: #f2f2f7;
    font-weight: 500;
    font-size: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 14px;
}
QPushButton#secondary_action:hover {
    background-color: #2c2c2e;
    border: 1px solid rgba(255, 255, 255, 0.14);
}

/* Small Tag Button */
QPushButton#tag_btn {
    background-color: #242428;
    color: #d1d1d6;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
}
QPushButton#tag_btn:hover {
    background-color: #ff453a;
    color: #ffffff;
    border-color: #ff453a;
}

/* Inputs & Dropdowns */
QComboBox {
    background-color: #1c1c1e;
    color: #f2f2f7;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 12px;
}
QComboBox:hover {
    border-color: rgba(255, 255, 255, 0.15);
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1c1c1e;
    color: #f2f2f7;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    selection-background-color: #0a84ff;
    outline: none;
    padding: 4px;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.2);
    min-height: 24px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.35);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""