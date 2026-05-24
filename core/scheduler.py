import threading
import time
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from core.audio_capture import AudioCapture
from core.adaptive_vad import AdaptiveVADController
from core.asr_engine import ASREngine
from core.streaming_asr import StreamingASREngine
from core.llm_corrector import LLMCorrector
from core.text_injector import TextInjector
from core.history_logger import HistoryLogger
from core.audio_features import AudioFeatureExtractor, SpeechQualityAssessor
from core.statistics import stats
from utils.logger import logger
from utils.config import Config


class Scheduler(QObject):
    sig_listening = pyqtSignal()
    sig_volume = pyqtSignal(float)
    sig_processing = pyqtSignal()
    sig_result = pyqtSignal(str)
    sig_hide = pyqtSignal(float)
    sig_error = pyqtSignal(str)
    sig_continuous_toggle = pyqtSignal(bool)
    sig_features = pyqtSignal(object)
    sig_noise_info = pyqtSignal(object)
    sig_vad_info = pyqtSignal(object)
    sig_streaming_text = pyqtSignal(str, bool)

    def __init__(self, use_adaptive_vad=True):
        super().__init__()
        self.audio = AudioCapture()
        self.vad = AdaptiveVADController(use_adaptive=use_adaptive_vad)
        self.asr = ASREngine()
        self.streaming_asr = StreamingASREngine()
        self.llm = LLMCorrector()
        self.injector = TextInjector()
        self.history = HistoryLogger(mode="normal")
        self.history_continuous = HistoryLogger(mode="continuous")
        self.feature_extractor = AudioFeatureExtractor()
        self.quality_assessor = SpeechQualityAssessor()

        self.is_running = False
        self.is_enabled = True
        self.continuous_mode = Config.CONTINUOUS_MODE
        self._thread = None
        self._lock = threading.Lock()
        self._continuous_start_time = 0
        self._max_continuous_duration = 300
        self._continuous_audio_buffer = []
        self._use_adaptive_vad = use_adaptive_vad

        self.streaming_asr.set_callback("on_partial", self._on_streaming_partial)
        self.streaming_asr.set_callback("on_final", self._on_streaming_final)

    def start(self):
        with self._lock:
            if self.is_running or not self.is_enabled:
                return
            self.is_running = True
            self.vad.reset()
            self._continuous_audio_buffer = []
            if self.continuous_mode:
                self._continuous_start_time = time.time()
                logger.info(f"Continuous mode started (max {self._max_continuous_duration}s, mic stays open)")
            self.audio.start()
            self.sig_listening.emit()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self, force_continuous=None):
        with self._lock:
            was_continuous = force_continuous if force_continuous is not None else self.continuous_mode
            buffer_size = len(self._continuous_audio_buffer)
            logger.info(f"stop() called: continuous={was_continuous}, buffer_size={buffer_size}, running={self.is_running}")
            self.is_running = False
            self.audio.stop()

            if was_continuous and buffer_size > 0:
                logger.info(f"Processing {buffer_size} audio chunks from continuous mode")
                audio_data = np.concatenate(self._continuous_audio_buffer)
                logger.info(f"Audio data shape: {audio_data.shape}, duration: {len(audio_data)/16000:.1f}s")
                self._continuous_audio_buffer = []
                threading.Thread(target=self._process_continuous_audio, args=(audio_data,), daemon=True).start()
            else:
                logger.warning(f"NOT processing: was_continuous={was_continuous}, buffer_size={buffer_size}")
                self._continuous_audio_buffer = []

            if was_continuous:
                logger.info(f"Continuous mode stopped after {time.time() - self._continuous_start_time:.0f}s")
            self.sig_hide.emit(0.1)

    def toggle_continuous(self):
        was_continuous = self.continuous_mode
        self.continuous_mode = not self.continuous_mode
        logger.info(f"Continuous mode: {'ON' if self.continuous_mode else 'OFF'}")
        self.sig_continuous_toggle.emit(self.continuous_mode)

        if self.continuous_mode:
            self.start()
        else:
            self.stop(was_continuous)
        return self.continuous_mode

    def toggle_enabled(self):
        self.is_enabled = not self.is_enabled
        status = "enabled" if self.is_enabled else "disabled"
        logger.info(f"Voice recognition {status}")
        if not self.is_enabled:
            self.stop()
        return self.is_enabled

    def _loop(self):
        consecutive_errors = 0
        max_consecutive_errors = 5
        chunk_count = 0

        while self.is_running:
            if self.continuous_mode and self._continuous_start_time > 0:
                elapsed = time.time() - self._continuous_start_time
                if elapsed >= self._max_continuous_duration:
                    logger.info(f"Continuous mode reached max duration ({self._max_continuous_duration}s)")
                    self.is_running = False
                    self.audio.stop()
                    break

            chunk = self.audio.get_chunk()
            if chunk is None:
                continue

            chunk_count += 1
            if chunk_count % 100 == 0:
                logger.info(f"Collected {chunk_count} chunks, buffer size: {len(self._continuous_audio_buffer)}")

            self.sig_volume.emit(float(np.abs(chunk).mean()))

            features = self.feature_extractor.compute_all_features(chunk)
            self.sig_features.emit(features)

            try:
                res = self.vad.process(chunk)
                consecutive_errors = 0

                noise_info = res.get("noise_info", {})
                quality = self.quality_assessor.assess_quality(
                    chunk, noise_info.get("noise_level", 0)
                )
                noise_info["quality"] = quality["quality_level"]
                self.sig_noise_info.emit(noise_info)
                self.sig_vad_info.emit(res)

                if self.continuous_mode:
                    self._continuous_audio_buffer.append(chunk.copy())
                    self.streaming_asr.feed_audio(chunk)
                    continue

                if res["is_end"]:
                    self.audio.stop()
                    self.is_running = False
                    self.sig_processing.emit()
                    threading.Thread(target=self._process, args=(res["audio"],), daemon=True).start()

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"VAD error: {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many errors, attempting recovery...")
                    self._recover()
                    consecutive_errors = 0

    def _process(self, audio: np.ndarray):
        try:
            raw_text = self.asr.transcribe(audio)
            if not raw_text:
                self.sig_result.emit("(No speech detected)")
                self.sig_hide.emit(2.0)
                return

            final_text = self.llm.correct(raw_text)
            self.injector.inject(final_text)
            self.history.log(final_text)
            stats.record_session(final_text)
            self.sig_result.emit(final_text)
            self.sig_hide.emit(3.0)

        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.sig_error.emit(f"Error: {str(e)}")
            self.sig_result.emit(f"Error: {str(e)}")
            self.sig_hide.emit(3.0)

    def _process_continuous_audio(self, audio: np.ndarray):
        self.sig_processing.emit()
        try:
            logger.info(f"Transcribing {len(audio)} samples ({len(audio)/16000:.1f}s of audio)")
            raw_text = self.asr.transcribe(audio)
            if not raw_text:
                self.sig_result.emit("(No speech detected in continuous mode)")
                self.sig_hide.emit(2.0)
                return

            final_text = self.llm.correct(raw_text)
            self.injector.inject(final_text)
            self.history_continuous.log(final_text)
            stats.record_session(final_text)
            self.sig_result.emit(final_text)
            self.sig_hide.emit(3.0)
            logger.info(f"Continuous mode result: {final_text}")

        except Exception as e:
            logger.error(f"Continuous processing error: {e}")
            self.sig_error.emit(f"Error: {str(e)}")
            self.sig_result.emit(f"Error: {str(e)}")
            self.sig_hide.emit(3.0)

    def _on_streaming_partial(self, text: str):
        self.sig_streaming_text.emit(text, False)

    def _on_streaming_final(self, text: str):
        self.sig_streaming_text.emit(text, True)

    def _recover(self):
        logger.info("Attempting audio recovery...")
        was_continuous = self.continuous_mode
        self.audio.stop()
        time.sleep(0.5)
        if self.audio.recover():
            logger.info("Recovery successful")
        else:
            self.sig_error.emit("Microphone recovery failed. Please restart the application.")
            self.is_running = False
