import sys
from PyQt6.QtWidgets import QApplication
from core.scheduler import Scheduler
from ui.overlay_window import OverlayWindow
from ui.tray_manager import TrayManager
from ui.analysis_window import VisualizationWindow
from utils.logger import logger
from utils.config import Config


def main():
    logger.info("VoiceIME Pro starting...")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    overlay = OverlayWindow()
    scheduler = Scheduler(use_adaptive_vad=True)
    analysis_window = VisualizationWindow()

    scheduler.sig_listening.connect(overlay.show_listening)
    scheduler.sig_volume.connect(overlay.update_volume)
    scheduler.sig_processing.connect(overlay.show_processing)
    scheduler.sig_result.connect(overlay.show_result)
    scheduler.sig_hide.connect(overlay.schedule_hide)
    scheduler.sig_error.connect(overlay.show_error)

    scheduler.sig_features.connect(analysis_window.update_features)
    scheduler.sig_noise_info.connect(analysis_window.update_noise_info)
    scheduler.sig_vad_info.connect(analysis_window.update_vad_info)
    scheduler.sig_streaming_text.connect(analysis_window.update_streaming_text)
    scheduler.sig_incremental_text.connect(analysis_window.append_incremental_text)
    scheduler.sig_command_executed.connect(analysis_window.show_command)

    tray = TrayManager(scheduler, analysis_window)

    logger.info("=" * 50)
    logger.info("VoiceIME Pro ready!")
    logger.info(f"Hold [{Config.HOTKEY.upper()}] to record")
    logger.info(f"Press [{Config.EXIT_KEY.upper()}] to exit")
    logger.info(f"Press [F9] for settings, [F10] for continuous mode")
    logger.info(f"Press [F11] for audio analysis window")
    logger.info("=" * 50)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
