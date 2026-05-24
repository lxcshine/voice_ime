from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)
        self.label = QLabel("VoiceIME Pro")
        self.label.setFont(QFont("Microsoft YaHei", 12))
        self.label.setStyleSheet("""
            QLabel {
                background: rgba(20, 20, 20, 0.85);
                color: #00ff88;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #333;
            }
        """)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() // 2 - 250, screen.height() - 120)

    def show_listening(self):
        self.label.setText("Listening... (speak, auto-input when done)")
        self.label.setStyleSheet(self.label.styleSheet().replace("#00ff88", "#ff4444"))
        self.show()

    def update_volume(self, level):
        bar_length = int(min(level * 300, 20))
        bar = "#" * bar_length + "-" * (20 - bar_length)
        self.label.setText(f"Listening [{bar}]")

    def show_processing(self):
        self.label.setText("Processing & correcting...")
        self.label.setStyleSheet(self.label.styleSheet().replace("#ff4444", "#ffaa00"))

    def show_result(self, text):
        self.label.setText(f"Done: {text}")
        self.label.setStyleSheet(self.label.styleSheet().replace("#ffaa00", "#00ff88").replace("#ff4444", "#00ff88"))

    def show_error(self, text):
        self.label.setText(f"Error: {text}")
        self.label.setStyleSheet(self.label.styleSheet().replace("#ffaa00", "#ff4444").replace("#00ff88", "#ff4444"))

    def schedule_hide(self, delay_sec):
        QTimer.singleShot(int(delay_sec * 1000), self.hide)
