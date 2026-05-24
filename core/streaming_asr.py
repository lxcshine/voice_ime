import numpy as np
import threading
import time
from funasr import AutoModel
from utils.logger import logger
from utils.config import Config


class StreamingASREngine:
    """
    Streaming ASR with incremental recognition for real-time subtitle output.
    Uses chunked audio processing with overlapping windows for continuous recognition.
    """

    def __init__(self):
        self.model = None
        self._model_lock = threading.Lock()
        self._is_loading = False

        self.chunk_duration = 2.0  # seconds per chunk for streaming
        self.overlap_duration = 0.5  # overlap between chunks
        self.sr = Config.SAMPLE_RATE
        self.chunk_size = int(self.chunk_duration * self.sr)
        self.overlap_size = int(self.overlap_duration * self.sr)

        self.audio_buffer = np.array([], dtype=np.float32)
        self.last_processed_idx = 0
        self.is_streaming = False

        self._stream_thread = None
        self._stop_event = threading.Event()

        self.callbacks = {
            "on_partial": None,
            "on_final": None,
            "on_error": None
        }

    def load_model(self):
        if self.model is not None:
            return
        with self._model_lock:
            if self._is_loading:
                return
            self._is_loading = True

        try:
            logger.info("Loading FunASR model for streaming ASR...")
            self.model = AutoModel(
                model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
                vad_model="fsmn-vad",
                punc_model="ct-punc-c",
                device="cuda:0" if self._check_cuda() else "cpu",
                disable_update=True
            )
            logger.info("Streaming ASR model loaded")
        except Exception as e:
            logger.error(f"Failed to load streaming ASR model: {e}")
        finally:
            self._is_loading = False

    def _check_cuda(self):
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def set_callback(self, name, func):
        if name in self.callbacks:
            self.callbacks[name] = func

    def start_streaming(self):
        self.audio_buffer = np.array([], dtype=np.float32)
        self.last_processed_idx = 0
        self.is_streaming = True
        self._stop_event.clear()
        self._stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._stream_thread.start()
        logger.info("Streaming ASR started")

    def stop_streaming(self):
        self.is_streaming = False
        self._stop_event.set()
        if self._stream_thread:
            self._stream_thread.join(timeout=2.0)
        logger.info("Streaming ASR stopped")

    def feed_audio(self, chunk: np.ndarray):
        if not self.is_streaming:
            return
        self.audio_buffer = np.concatenate([self.audio_buffer, chunk])

    def _stream_loop(self):
        while self.is_streaming and not self._stop_event.is_set():
            if len(self.audio_buffer) - self.last_processed_idx < self.chunk_size:
                time.sleep(0.1)
                continue

            end_idx = self.last_processed_idx + self.chunk_size
            chunk = self.audio_buffer[self.last_processed_idx:end_idx]

            self._process_chunk(chunk, is_final=False)

            self.last_processed_idx = end_idx - self.overlap_size

    def _process_chunk(self, audio: np.ndarray, is_final=False):
        if self.model is None:
            self.load_model()
        if self.model is None:
            return

        try:
            import noisereduce as nr
            audio_clean = nr.reduce_noise(y=audio, sr=self.sr, prop_decrease=0.5)

            res = self.model.generate(
                input=audio_clean,
                batch_size_s=300,
                use_itn=True,
                is_final=is_final
            )

            if res and len(res) > 0 and "text" in res[0]:
                text = res[0]["text"].strip()
                if text:
                    if is_final:
                        if self.callbacks["on_final"]:
                            self.callbacks["on_final"](text)
                    else:
                        if self.callbacks["on_partial"]:
                            self.callbacks["on_partial"](text)

        except Exception as e:
            logger.error(f"Streaming ASR error: {e}")
            if self.callbacks["on_error"]:
                self.callbacks["on_error"](str(e))

    def process_final(self, audio: np.ndarray) -> str:
        if self.model is None:
            self.load_model()
        if self.model is None:
            return ""

        try:
            import noisereduce as nr
            audio_clean = nr.reduce_noise(y=audio, sr=self.sr, prop_decrease=0.8)

            res = self.model.generate(
                input=audio_clean,
                batch_size_s=300,
                use_itn=True,
                is_final=True
            )

            if res and len(res) > 0 and "text" in res[0]:
                return res[0]["text"].strip()
            return ""
        except Exception as e:
            logger.error(f"Final ASR error: {e}")
            return ""
