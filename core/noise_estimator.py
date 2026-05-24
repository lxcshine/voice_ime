import numpy as np
from scipy.signal import welch
from utils.logger import logger


class NoiseEstimator:
    """
    Adaptive noise estimation using Minimum Statistics and Exponential Moving Average.
    Implements spectral subtraction-based noise tracking for dynamic VAD threshold.
    """

    def __init__(self, sr=16000, frame_size=512, alpha=0.95, beta=0.02):
        self.sr = sr
        self.frame_size = frame_size
        self.alpha = alpha  # EMA smoothing factor for noise estimate
        self.beta = beta    # Minimum tracking factor

        self.noise_estimate = None
        self.noise_var = None
        self.is_initialized = False
        self.min_noise = None
        self.frame_count = 0
        self.noise_history = []
        self.history_size = 50

    def update(self, frame: np.ndarray) -> dict:
        self.frame_count += 1

        frame_energy = float(np.mean(frame ** 2))
        frame_rms = float(np.sqrt(frame_energy + 1e-10))

        if not self.is_initialized:
            self.noise_estimate = frame_energy
            self.noise_var = frame_energy * 0.1
            self.min_noise = frame_energy
            self.is_initialized = True
            return {
                "noise_level": self.noise_estimate,
                "snr": 0.0,
                "threshold": 0.5,
                "is_noise_only": True
            }

        self.noise_history.append(frame_energy)
        if len(self.noise_history) > self.history_size:
            self.noise_history.pop(0)

        if frame_energy < self.noise_estimate:
            self.noise_estimate = self.alpha * self.noise_estimate + (1 - self.alpha) * frame_energy
        else:
            self.noise_estimate = self.alpha * self.noise_estimate + (1 - self.alpha) * self.noise_estimate

        if frame_energy < self.min_noise:
            self.min_noise = frame_energy
        elif self.frame_count % 100 == 0:
            self.min_noise = min(self.noise_history[-20:]) if len(self.noise_history) >= 20 else self.noise_estimate

        snr_db = 10 * np.log10(frame_energy / (self.noise_estimate + 1e-10) + 1e-10)

        threshold = self._compute_adaptive_threshold(snr_db)

        is_noise_only = frame_energy < self.noise_estimate * 2.0

        return {
            "noise_level": float(self.noise_estimate),
            "snr": float(snr_db),
            "threshold": float(threshold),
            "is_noise_only": bool(is_noise_only),
            "frame_energy": float(frame_energy),
            "frame_rms": float(frame_rms)
        }

    def _compute_adaptive_threshold(self, snr_db: float) -> float:
        base_threshold = 0.5

        if snr_db < 0:
            threshold = base_threshold + 0.2
        elif snr_db < 5:
            threshold = base_threshold + 0.1
        elif snr_db < 15:
            threshold = base_threshold
        elif snr_db < 25:
            threshold = base_threshold - 0.1
        else:
            threshold = base_threshold - 0.15

        return float(np.clip(threshold, 0.2, 0.7))

    def get_snr(self, frame: np.ndarray) -> float:
        frame_energy = float(np.mean(frame ** 2))
        if self.noise_estimate is None or self.noise_estimate < 1e-10:
            return 0.0
        snr_db = 10 * np.log10(frame_energy / (self.noise_estimate + 1e-10) + 1e-10)
        return float(snr_db)

    def get_noise_spectrum(self) -> np.ndarray:
        if self.noise_estimate is None:
            return np.zeros(self.frame_size // 2 + 1)
        return np.ones(self.frame_size // 2 + 1) * self.noise_estimate
