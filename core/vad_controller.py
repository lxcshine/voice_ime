import torch
import numpy as np
from silero_vad import load_silero_vad
from utils.config import Config


class VADController:
    def __init__(self):
        self.model = load_silero_vad()
        self.sr = Config.SAMPLE_RATE
        self.threshold = Config.VAD_THRESHOLD
        self.min_silence_samples = int(0.6 * self.sr)  # 600ms 静音断句

        self.is_speaking = False
        self.silence_counter = 0
        self.speech_buffer = []

    def process(self, chunk: np.ndarray) -> dict:
        tensor = torch.from_numpy(chunk).float()
        if len(tensor) < 512:
            tensor = torch.nn.functional.pad(tensor, (0, 512 - len(tensor)))

        speech_prob = self.model(tensor, self.sr).item()
        is_speech = speech_prob > self.threshold

        if is_speech:
            self.is_speaking = True
            self.silence_counter = 0
            self.speech_buffer.extend(chunk.tolist())
        elif self.is_speaking:
            self.silence_counter += len(chunk)
            self.speech_buffer.extend(chunk.tolist())

            if self.silence_counter >= self.min_silence_samples:
                utterance = np.array(self.speech_buffer, dtype=np.float32)
                self.reset()
                return {"is_end": True, "audio": utterance}

        return {"is_end": False, "audio": None}

    def reset(self):
        self.is_speaking = False
        self.silence_counter = 0
        self.speech_buffer = []
        self.model.reset_states()
