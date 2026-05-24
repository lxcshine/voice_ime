from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from ui.visualization import SpectrumDisplay, WaveformDisplay, StatusIndicator, MetricsPanel, StreamingTextDisplay
from utils.logger import logger


class VisualizationWindow(QMainWindow):
    """
    Main visualization window for audio features, VAD status, and streaming ASR.
    Shows real-time spectrum, waveform, noise level, and adaptive threshold.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoiceIME Pro - Audio Analysis")
        self.resize(800, 600)
        self.setStyleSheet("background: #1a1a1a;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("VoiceIME Pro - Real-time Audio Analysis")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #00ff88; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        top_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        self.waveform = WaveformDisplay()
        left_panel.addWidget(QLabel("Waveform"))
        left_panel.addWidget(self.waveform)

        self.spectrum = SpectrumDisplay()
        left_panel.addWidget(QLabel("FFT Spectrum"))
        left_panel.addWidget(self.spectrum)

        self.mel_spectrum = SpectrumDisplay()
        left_panel.addWidget(QLabel("Mel Spectrum"))
        left_panel.addWidget(self.mel_spectrum)

        top_layout.addLayout(left_panel, 2)

        right_panel = QVBoxLayout()
        self.vad_status = StatusIndicator("VAD Status")
        right_panel.addWidget(self.vad_status)

        self.mic_status = StatusIndicator("Microphone")
        right_panel.addWidget(self.mic_status)

        self.mode_status = StatusIndicator("Mode")
        right_panel.addWidget(self.mode_status)

        self.metrics = MetricsPanel()
        right_panel.addWidget(self.metrics)

        top_layout.addLayout(right_panel, 1)
        layout.addLayout(top_layout)

        self.streaming_text = StreamingTextDisplay()
        layout.addWidget(QLabel("Streaming Recognition:"))
        layout.addWidget(self.streaming_text)

        bottom_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("Open Visualization")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: #2d2d2d; color: #00ff88;
                padding: 8px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #3d3d3d; }
        """)
        bottom_layout.addWidget(self.toggle_btn)

        self.adaptive_label = QLabel("Adaptive VAD: ON")
        self.adaptive_label.setStyleSheet("color: #aaa; font-size: 11px;")
        bottom_layout.addWidget(self.adaptive_label)

        layout.addLayout(bottom_layout)

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(50)

        self._current_features = {}
        self._current_noise = {}
        self._current_vad_info = {}

    def update_features(self, features: dict):
        self._current_features = features

    def update_noise_info(self, noise_info: dict):
        self._current_noise = noise_info

    def update_vad_info(self, vad_info: dict):
        self._current_vad_info = vad_info

    def update_streaming_text(self, text: str, is_final=False):
        if is_final:
            self.streaming_text.update_final(text)
        else:
            self.streaming_text.update_partial(text)

    def set_vad_status(self, status: str, color: QColor):
        self.vad_status.set_status(status, color)

    def set_mic_status(self, status: str, color: QColor):
        self.mic_status.set_status(status, color)

    def set_mode(self, mode: str):
        color = QColor(0, 255, 136) if mode == "Continuous" else QColor(100, 150, 255)
        self.mode_status.set_status(mode, color)

    def set_adaptive_mode(self, enabled: bool):
        self.adaptive_label.setText(f"Adaptive VAD: {'ON' if enabled else 'OFF'}")
        self.adaptive_label.setStyleSheet(
            f"color: {'#00ff88' if enabled else '#ff4444'}; font-size: 11px;"
        )

    def _update_display(self):
        if "fft_spectrum" in self._current_features:
            self.spectrum.update_spectrum(self._current_features["fft_spectrum"], "fft")
        if "mel_spectrum" in self._current_features:
            self.mel_spectrum.update_spectrum(self._current_features["mel_spectrum"], "mel")

        if self._current_noise:
            snr = self._current_noise.get("snr", 0)
            noise = self._current_noise.get("noise_level", 0)
            threshold = self._current_noise.get("threshold", 0.5)
            self.metrics.update_metrics(
                snr=snr,
                noise=noise,
                threshold=threshold,
                quality=self._current_noise.get("quality", "Fair")
            )
