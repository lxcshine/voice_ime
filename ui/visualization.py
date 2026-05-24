from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QLinearGradient
import numpy as np


class SpectrumDisplay(QWidget):
    """Real-time FFT spectrum visualization with gradient colors."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.spectrum = np.zeros(256)
        self.mel_spectrum = np.zeros(40)
        self.setFixedHeight(120)
        self.setMinimumWidth(300)
        self.display_mode = "fft"  # fft or mel

    def update_spectrum(self, spectrum: np.ndarray, mode="fft"):
        if mode == "fft":
            self.spectrum = spectrum[:256]
            self.display_mode = "fft"
        else:
            self.mel_spectrum = spectrum
            self.display_mode = "mel"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = QColor(30, 30, 30)
        painter.fillRect(self.rect(), bg_color)

        if self.display_mode == "fft":
            self._draw_fft(painter)
        else:
            self._draw_mel(painter)

    def _draw_fft(self, painter: QPainter):
        width = self.width()
        height = self.height()
        bar_width = max(1, width // len(self.spectrum) - 1)

        max_val = np.max(self.spectrum) + 1e-10

        for i, val in enumerate(self.spectrum):
            x = i * (bar_width + 1)
            bar_height = int((val / max_val) * height * 0.9)

            ratio = val / max_val
            if ratio > 0.7:
                color = QColor(255, 80, 80)
            elif ratio > 0.4:
                color = QColor(255, 200, 50)
            else:
                color = QColor(50, 200, 100)

            painter.fillRect(x, height - bar_height, bar_width, bar_height, color)

    def _draw_mel(self, painter: QPainter):
        width = self.width()
        height = self.height()
        bar_width = max(2, width // len(self.mel_spectrum) - 2)

        max_val = np.max(self.mel_spectrum) + 1e-10

        for i, val in enumerate(self.mel_spectrum):
            x = i * (bar_width + 2)
            bar_height = int((val / max_val) * height * 0.9)

            gradient = QLinearGradient(x, height, x, height - bar_height)
            gradient.setColorAt(0, QColor(50, 100, 255))
            gradient.setColorAt(1, QColor(200, 50, 255))

            painter.fillRect(x, height - bar_height, bar_width, bar_height, gradient)


class WaveformDisplay(QWidget):
    """Real-time audio waveform visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.waveform = np.zeros(512)
        self.setFixedHeight(80)
        self.setMinimumWidth(300)

    def update_waveform(self, data: np.ndarray):
        if len(data) > 512:
            step = len(data) // 512
            self.waveform = data[::step][:512]
        else:
            self.waveform[:len(data)] = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(20, 20, 20))

        width = self.width()
        height = self.height()
        mid_y = height // 2

        pen = QPen(QColor(0, 255, 136), 1.5)
        painter.setPen(pen)

        max_val = np.max(np.abs(self.waveform)) + 1e-10

        points = []
        for i, val in enumerate(self.waveform):
            x = int(i * width / len(self.waveform))
            y = int(mid_y - (val / max_val) * mid_y * 0.9)
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])


class StatusIndicator(QWidget):
    """Status indicator with colored dot and label."""

    def __init__(self, label="Status", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.status_text = "Idle"
        self.color = QColor(128, 128, 128)
        self.setFixedHeight(30)

    def set_status(self, text: str, color: QColor):
        self.status_text = text
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(30, 30, 30))

        painter.setBrush(self.color)
        painter.drawEllipse(10, 8, 14, 14)

        painter.setPen(QColor(200, 200, 200))
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.drawText(32, 20, f"{self.label_text}: {self.status_text}")


class MetricsPanel(QFrame):
    """Panel displaying real-time audio metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(30, 30, 30, 0.9); border-radius: 8px;")
        layout = QVBoxLayout(self)

        self.snr_label = self._create_metric("SNR", "-- dB")
        self.noise_label = self._create_metric("Noise Level", "--")
        self.threshold_label = self._create_metric("VAD Threshold", "--")
        self.quality_label = self._create_metric("Quality", "--")

        layout.addWidget(self.snr_label)
        layout.addWidget(self.noise_label)
        layout.addWidget(self.threshold_label)
        layout.addWidget(self.quality_label)

    def _create_metric(self, name: str, value: str) -> QLabel:
        label = QLabel(f"{name}: {value}")
        label.setStyleSheet("color: #aaa; font-size: 11px; padding: 2px;")
        return label

    def update_metrics(self, snr=None, noise=None, threshold=None, quality=None):
        if snr is not None:
            self.snr_label.setText(f"SNR: {snr:.1f} dB")
        if noise is not None:
            self.noise_label.setText(f"Noise Level: {noise:.5f}")
        if threshold is not None:
            self.threshold_label.setText(f"VAD Threshold: {threshold:.3f}")
        if quality is not None:
            self.quality_label.setText(f"Quality: {quality}")


class StreamingTextDisplay(QWidget):
    """
    Real-time streaming text display for incremental ASR output.
    Supports character-by-character animation and word-level diff display.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.partial_text = ""
        self.final_text = ""
        self._animation_queue = []
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._animate_next_char)
        self._anim_interval = 30
        self.setStyleSheet("background: rgba(20, 20, 20, 0.9); border-radius: 8px;")

        layout = QVBoxLayout(self)
        self.text_label = QLabel("Waiting for speech...")
        self.text_label.setStyleSheet("color: #666; font-size: 13px; padding: 5px;")
        self.text_label.setWordWrap(True)
        layout.addWidget(self.text_label)

    def update_partial(self, text: str):
        self.partial_text = text
        self.text_label.setText(f"[Recognizing] {text}")
        self.text_label.setStyleSheet("color: #ffaa00; font-size: 13px; padding: 5px;")

    def append_incremental(self, new_chars: str):
        if not new_chars:
            return
        self._animation_queue = list(new_chars)
        if not self._anim_timer.isActive():
            self._anim_timer.start(self._anim_interval)

    def _animate_next_char(self):
        if not self._animation_queue:
            self._anim_timer.stop()
            return

        chars_batch = []
        batch_size = max(1, len(self._animation_queue) // 3)
        for _ in range(batch_size):
            if not self._animation_queue:
                break
            chars_batch.append(self._animation_queue.pop(0))

        self.partial_text += "".join(chars_batch)
        self.text_label.setText(f"[Recognizing] {self.partial_text}")
        self.text_label.setStyleSheet("color: #ffaa00; font-size: 13px; padding: 5px;")

        if not self._animation_queue:
            self._anim_timer.stop()

    def update_final(self, text: str):
        self._animation_queue = []
        self._anim_timer.stop()
        self.final_text = text
        self.partial_text = text
        self.text_label.setText(f"[Done] {text}")
        self.text_label.setStyleSheet("color: #00ff88; font-size: 13px; padding: 5px;")

    def reset(self):
        self._animation_queue = []
        self._anim_timer.stop()
        self.partial_text = ""
        self.final_text = ""
        self.text_label.setText("Waiting for speech...")
        self.text_label.setStyleSheet("color: #666; font-size: 13px; padding: 5px;")
