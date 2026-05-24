import torch
import numpy as np
from silero_vad import load_silero_vad
from core.noise_estimator import NoiseEstimator
from utils.config import Config
from utils.logger import logger


class AdaptiveVADController:
    """
    Adaptive Voice Activity Detection with noise estimation and dynamic threshold.
    Combines Silero VAD neural network with traditional energy-based detection.
    """

    def __init__(self, use_adaptive=True):
        self.model = load_silero_vad()
        self.sr = Config.SAMPLE_RATE
        self.use_adaptive = use_adaptive

        self.fixed_threshold = Config.VAD_THRESHOLD
        self.adaptive_threshold = Config.VAD_THRESHOLD
        self.min_silence_samples = int(0.6 * self.sr)

        self.noise_estimator = NoiseEstimator(sr=self.sr)

        self.is_speaking = False
        self.silence_counter = 0
        self.speech_buffer = []

        self.stats = {
            "total_frames": 0,
            "speech_frames": 0,
            "noise_frames": 0,
            "avg_snr": 0.0,
            "snr_history": []
        }

    def process(self, chunk: np.ndarray) -> dict:
        self.stats["total_frames"] += 1

        noise_info = self.noise_estimator.update(chunk)

        if self.use_adaptive:
            self.adaptive_threshold = noise_info["threshold"]
            current_threshold = self.adaptive_threshold
        else:
            current_threshold = self.fixed_threshold

        tensor = torch.from_numpy(chunk).float()
        if len(tensor) < 512:
            tensor = torch.nn.functional.pad(tensor, (0, 512 - len(tensor)))

        speech_prob = self.model(tensor, self.sr).item()

        energy = float(np.mean(chunk ** 2))
        energy_threshold = noise_info["noise_level"] * 3.0
        energy_is_speech = energy > energy_threshold

        is_speech = (speech_prob > current_threshold) and energy_is_speech

        self.stats["snr_history"].append(noise_info["snr"])
        if len(self.stats["snr_history"]) > 100:
            self.stats["snr_history"].pop(0)
        self.stats["avg_snr"] = float(np.mean(self.stats["snr_history"]))

        if is_speech:
            self.is_speaking = True
            self.silence_counter = 0
            self.speech_buffer.append(chunk.copy())
            self.stats["speech_frames"] += 1
        elif self.is_speaking:
            self.silence_counter += len(chunk)
            self.speech_buffer.append(chunk.copy())

            if self.silence_counter >= self.min_silence_samples:
                utterance = np.concatenate(self.speech_buffer, axis=0)
                self.reset()
                return {
                    "is_end": True,
                    "audio": utterance,
                    "noise_info": noise_info,
                    "speech_prob": speech_prob,
                    "threshold": current_threshold
                }
            self.stats["noise_frames"] += 1
        else:
            self.stats["noise_frames"] += 1

        return {
            "is_end": False,
            "audio": None,
            "noise_info": noise_info,
            "speech_prob": speech_prob,
            "threshold": current_threshold
        }

    def reset(self):
        self.is_speaking = False
        self.silence_counter = 0
        self.speech_buffer = []
        self.model.reset_states()

    def get_stats(self) -> dict:
        return {
            "total_frames": self.stats["total_frames"],
            "speech_ratio": self.stats["speech_frames"] / max(self.stats["total_frames"], 1),
            "avg_snr": self.stats["avg_snr"],
            "adaptive_threshold": self.adaptive_threshold,
            "fixed_threshold": self.fixed_threshold,
            "noise_level": self.noise_estimator.noise_estimate if self.noise_estimator.noise_estimate else 0.0
        }
