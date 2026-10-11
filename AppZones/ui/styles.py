STYLESHEET = """
QMainWindow {
    background-color: #121214;
}
QWidget#central {
    background-color: #121214;
}

/* PowerToys Cards */
QFrame#card {
    background-color: #1c1c20;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
}
QFrame#card:hover {
    border: 1px solid rgba(255, 255, 255, 0.12);
}

QFrame#monitor_card {
    background-color: #1c1c20;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 6px 14px;
}

/* Typography */
QLabel {
    color: #f1f1f3;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', -apple-system, sans-serif;
    font-size: 13px;
}
QLabel#header_title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.3px;
}
QLabel#subtitle {
    font-size: 12px;
    color: #8c8c9a;
}
QLabel#field_label {
    font-size: 12px;
    color: #9d9da8;
    font-weight: 600;
}

/* Inputs & Dropdowns */
QComboBox, QLineEdit {
    background-color: #141416;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 7px;
    padding: 6px 10px;
    color: #ffffff;
    font-size: 13px;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QComboBox:hover, QLineEdit:hover {
    background-color: #19191c;
    border: 1px solid rgba(255, 255, 255, 0.18);
}
QComboBox:focus, QLineEdit:focus {
    background-color: #141416;
    border: 1px solid #0078d4;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #8e8e99;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1c1c20;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    color: #ffffff;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #242428;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 7px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 500;
    font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
}
QPushButton:hover {
    background-color: #2c2c32;
    border: 1px solid rgba(255, 255, 255, 0.16);
}
QPushButton:pressed {
    background-color: #1d1d21;
}

QPushButton#primary {
    background-color: #0078d4;
    border: 1px solid #1084d9;
    color: #ffffff;
    font-weight: 600;
    border-radius: 8px;
}
QPushButton#primary:hover {
    background-color: #1084d9;
    border: 1px solid #2993e3;
}
QPushButton#primary:pressed {
    background-color: #006cbe;
}

QPushButton#danger {
    background-color: transparent;
    color: #8c8c9a;
    border: 1px solid transparent;
    border-radius: 6px;
    font-size: 12px;
    padding: 4px 8px;
}
QPushButton#danger:hover {
    background-color: rgba(232, 17, 35, 0.15);
    color: #f87171;
    border: 1px solid rgba(232, 17, 35, 0.25);
}

QPushButton#secondary_action {
    background-color: #1d1d22;
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 7px;
}
QPushButton#secondary_action:hover {
    background-color: #26262c;
    border: 1px solid rgba(255, 255, 255, 0.18);
}

/* Dialog */
QDialog {
    background-color: #161619;
}
QListWidget {
    background-color: #121214;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 6px;
    color: #ffffff;
    font-size: 13px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 5px;
}
QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 0.06);
}
QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
"""