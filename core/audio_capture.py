import queue
import numpy as np
import sounddevice as sd
from utils.logger import logger
from utils.config import Config


class AudioCapture:
    def __init__(self):
        self.sr = Config.SAMPLE_RATE
        self.chunk_size = int(self.sr * 0.03)
        self.queue = queue.Queue(maxsize=100)
        self.stream = None
        self.device = self._find_best_device()
        self.error_count = 0
        self.max_errors = 3

    def _find_best_device(self):
        try:
            devices = sd.query_devices()
            default_input = sd.query_devices(kind='input')
            logger.info(f"Default input device: {default_input['name']}")

            logger.info("Available input devices:")
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    logger.info(f"  [{i}] {dev['name']}")

            return None

        except Exception as e:
            logger.error(f"Failed to query devices: {e}")
            return None

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
            self.error_count += 1

        data = indata[:, 0].astype(np.float32).copy()

        volume = float(np.abs(data).mean())
        if volume > 0.01:
            logger.debug(f"Volume: {volume:.5f}")

        try:
            self.queue.put_nowait(data)
        except queue.Full:
            pass

    def start(self):
        if self.stream is not None:
            return

        logger.info(f"Opening microphone (device: {self.device})")
        try:
            self.stream = sd.InputStream(
                samplerate=self.sr,
                channels=1,
                dtype="float32",
                blocksize=self.chunk_size,
                callback=self._callback,
                device=self.device
            )
            self.stream.start()
            self.error_count = 0
            logger.info("Microphone opened")
        except Exception as e:
            logger.error(f"Failed to open microphone: {e}")
            logger.info("Hint: Please check if microphone is disabled in system settings")
            raise

    def stop(self):
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.warning(f"Error closing stream: {e}")
            finally:
                self.stream = None
                logger.info("Microphone closed")

    def recover(self):
        self.stop()
        self.queue = queue.Queue(maxsize=100)
        try:
            self.start()
            logger.info("Microphone recovered successfully")
            return True
        except Exception as e:
            logger.error(f"Microphone recovery failed: {e}")
            return False

    def get_chunk(self, timeout=0.05):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def check_health(self):
        if self.error_count >= self.max_errors:
            logger.warning(f"Audio errors exceeded threshold ({self.error_count}/{self.max_errors})")
            return False
        return True
