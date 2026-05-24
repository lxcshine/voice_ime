from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from pynput import keyboard
from utils.logger import logger
from utils.config import settings, Config
from core.statistics import stats


class TrayManager(QObject):
    sig_show_settings = pyqtSignal()
    sig_show_stats = pyqtSignal()
    sig_show_analysis = pyqtSignal()
    sig_exit = pyqtSignal()
    sig_toggle_continuous = pyqtSignal()

    def __init__(self, scheduler, analysis_window=None):
        super().__init__()
        self.scheduler = scheduler
        self.analysis_window = analysis_window
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon.fromTheme("audio-input-microphone", QIcon()))
        self.tray.setToolTip("VoiceIME Pro - Ready")

        self.continuous_action = None
        self.enabled_action = None
        self.stats_action = None

        self._build_menu()
        self.tray.show()

        self.listener = None
        self._setup_hotkey()

        self.sig_show_settings.connect(self._show_settings_dialog)
        self.sig_show_stats.connect(self._show_stats_dialog)
        self.sig_show_analysis.connect(self._show_analysis)
        self.sig_exit.connect(QApplication.quit)
        self.sig_toggle_continuous.connect(self._do_toggle_continuous)

    def _build_menu(self):
        menu = QMenu()

        title = menu.addAction("VoiceIME Pro")
        title.setEnabled(False)
        menu.addSeparator()

        self.continuous_action = QAction("Continuous Mode: OFF", triggered=self._toggle_continuous)
        menu.addAction(self.continuous_action)

        self.enabled_action = QAction("Enable Voice Recognition", triggered=self._toggle_enabled)
        menu.addAction(self.enabled_action)

        menu.addSeparator()

        self.stats_action = QAction("Show Statistics", triggered=self._show_stats)
        menu.addAction(self.stats_action)

        settings_action = QAction("Settings (F9)", triggered=self._show_settings)
        menu.addAction(settings_action)

        analysis_action = QAction("Audio Analysis (F11)", triggered=self._show_analysis)
        menu.addAction(analysis_action)

        menu.addSeparator()
        menu.addAction(QAction("Exit (F12)", triggered=QApplication.quit))

        self.tray.setContextMenu(menu)

    def _toggle_continuous(self):
        self.sig_toggle_continuous.emit()

    def _do_toggle_continuous(self):
        is_on = self.scheduler.toggle_continuous()
        self.continuous_action.setText(f"Continuous Mode: {'ON' if is_on else 'OFF'}")

    def _toggle_enabled(self):
        is_on = self.scheduler.toggle_enabled()
        self.enabled_action.setText(f"{'Disable' if is_on else 'Enable'} Voice Recognition")
        self.tray.setToolTip(f"VoiceIME Pro - {'Enabled' if is_on else 'Disabled'}")

    def _show_stats(self):
        self.sig_show_stats.emit()

    def _show_stats_dialog(self):
        summary = stats.get_summary()
        msg = (
            f"Today: {summary['today_chars']} chars, {summary['today_sessions']} sessions\n"
            f"Total: {summary['total_chars']} chars, {summary['total_sessions']} sessions\n"
            f"Session time: {summary['session_duration']}\n"
            f"Avg accuracy: {summary['avg_accuracy']}"
        )
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("VoiceIME Statistics")
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def _show_settings(self):
        self.sig_show_settings.emit()

    def _show_analysis(self):
        if self.analysis_window:
            self.analysis_window.show()
            self.analysis_window.raise_()
            self.analysis_window.activateWindow()

    def _show_settings_dialog(self):
        msg = (
            f"Current Settings:\n\n"
            f"Hotkey: {settings.get('hotkey', 'f8').upper()}\n"
            f"Exit key: {settings.get('exit_key', 'f12').upper()}\n"
            f"VAD threshold: {settings.get('vad_threshold', 0.5)}\n"
            f"LLM correction: {'ON' if settings.get('llm_enabled', True) else 'OFF'}\n"
            f"Continuous mode: {'ON' if settings.get('continuous_mode', False) else 'OFF'}\n"
            f"Auto punctuation: {'ON' if settings.get('auto_punctuation', True) else 'OFF'}\n"
            f"Space append: {'ON' if settings.get('space_append', True) else 'OFF'}\n\n"
            f"Edit settings.json to change."
        )
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("VoiceIME Settings")
        msg_box.setText(msg)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def _get_base_key(self, k):
        if k in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return "ctrl"
        if k in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            return "alt"
        if k in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            return "shift"
        if hasattr(k, 'char') and k.char:
            return k.char.lower()
        if hasattr(k, 'name'):
            return k.name.lower()
        return str(k).replace("Key.", "").lower()

    def _setup_hotkey(self):
        target_keys = set(k.strip().lower() for k in Config.HOTKEY.split("+"))
        exit_key = settings.get("exit_key", "f12").lower()
        settings_key = "f9"
        continuous_key = "f10"
        analysis_key = "f11"

        self.pressed_keys = set()

        logger.info(f"Hotkey: {Config.HOTKEY.upper()}, Exit: {exit_key.upper()}, Settings: {settings_key.upper()}")

        def on_press(key):
            base_key = self._get_base_key(key)
            self.pressed_keys.add(base_key)

            if base_key == exit_key:
                logger.info("=== Voice recognition exited ===")
                self.sig_exit.emit()
                return False

            if base_key == settings_key:
                self.sig_show_settings.emit()
                return

            if base_key == continuous_key:
                self.sig_toggle_continuous.emit()
                return

            if base_key == analysis_key:
                self.sig_show_analysis.emit()
                return

            if target_keys.issubset(self.pressed_keys):
                logger.info(f"Hotkey triggered! Starting recording...")
                self.scheduler.start()

        def on_release(key):
            base_key = self._get_base_key(key)
            if base_key in self.pressed_keys:
                self.pressed_keys.remove(base_key)

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        logger.info(f"Keyboard listener started. Press {Config.HOTKEY.upper()} to record.")

    def stop(self):
        if self.listener:
            self.listener.stop()
