import numpy as np
from scipy.signal import welch, stft
from utils.logger import logger


class AudioFeatureExtractor:
    """
    Audio feature extraction for visualization and quality assessment.
    Computes FFT spectrum, Mel-spectrum, ZCR, RMS energy, and spectral features.
    """

    def __init__(self, sr=16000, frame_size=512, hop_length=256, n_mels=40):
        self.sr = sr
        self.frame_size = frame_size
        self.hop_length = hop_length
        self.n_mels = n_mels

        self.mel_filterbank = self._create_mel_filterbank()

    def _create_mel_filterbank(self) -> np.ndarray:
        mel_freqs = self._hz_to_mel(np.linspace(self._mel_to_hz(0), self._mel_to_hz(self.sr // 2), self.n_mels + 2))
        bins = np.floor((self.frame_size + 1) * mel_freqs / self.sr).astype(int)
        bins = np.clip(bins, 0, self.frame_size // 2)

        filterbank = np.zeros((self.n_mels, self.frame_size // 2 + 1))
        for m in range(1, self.n_mels + 1):
            for k in range(bins[m - 1], bins[m]):
                if bins[m] != bins[m - 1]:
                    filterbank[m - 1, k] = (k - bins[m - 1]) / (bins[m] - bins[m - 1] + 1e-10)
            for k in range(bins[m], bins[m + 1]):
                if bins[m + 1] != bins[m]:
                    filterbank[m - 1, k] = (bins[m + 1] - k) / (bins[m + 1] - bins[m] + 1e-10)
        return filterbank

    @staticmethod
    def _hz_to_mel(hz):
        return 2595.0 * np.log10(1.0 + hz / 700.0)

    @staticmethod
    def _mel_to_hz(mel):
        return 700.0 * (10.0 ** (mel / 2595.0) - 1.0)

    def compute_fft_spectrum(self, frame: np.ndarray) -> np.ndarray:
        if len(frame) < self.frame_size:
            frame = np.pad(frame, (0, self.frame_size - len(frame)))
        spectrum = np.fft.rfft(frame * np.hanning(len(frame)))
        return np.abs(spectrum)

    def compute_mel_spectrum(self, frame: np.ndarray) -> np.ndarray:
        power_spectrum = self.compute_fft_spectrum(frame) ** 2
        mel_spectrum = np.dot(self.mel_filterbank, power_spectrum[:self.frame_size // 2 + 1])
        return np.log10(mel_spectrum + 1e-10)

    def compute_zcr(self, frame: np.ndarray) -> float:
        zcr = np.sum(np.abs(np.diff(np.signbit(frame)))) / (2 * len(frame))
        return float(zcr)

    def compute_rms(self, frame: np.ndarray) -> float:
        return float(np.sqrt(np.mean(frame ** 2)))

    def compute_spectral_centroid(self, frame: np.ndarray) -> float:
        if len(frame) < self.frame_size:
            frame = np.pad(frame, (0, self.frame_size - len(frame)))
        spectrum = np.abs(np.fft.rfft(frame * np.hanning(len(frame))))
        freqs = np.fft.rfftfreq(len(frame), 1.0 / self.sr)
        centroid = np.sum(freqs * spectrum) / (np.sum(spectrum) + 1e-10)
        return float(centroid)

    def compute_spectral_rolloff(self, frame: np.ndarray, roll_percent=0.85) -> float:
        if len(frame) < self.frame_size:
            frame = np.pad(frame, (0, self.frame_size - len(frame)))
        spectrum = np.abs(np.fft.rfft(frame * np.hanning(len(frame))))
        cumsum = np.cumsum(spectrum)
        total = cumsum[-1] + 1e-10
        rolloff = np.searchsorted(cumsum, roll_percent * total)
        freqs = np.fft.rfftfreq(len(frame), 1.0 / self.sr)
        return float(freqs[min(rolloff, len(freqs) - 1)])

    def compute_all_features(self, frame: np.ndarray) -> dict:
        return {
            "fft_spectrum": self.compute_fft_spectrum(frame),
            "mel_spectrum": self.compute_mel_spectrum(frame),
            "zcr": self.compute_zcr(frame),
            "rms": self.compute_rms(frame),
            "spectral_centroid": self.compute_spectral_centroid(frame),
            "spectral_rolloff": self.compute_spectral_rolloff(frame)
        }


class SpeechQualityAssessor:
    """
    Speech quality assessment using SNR, PESQ-like metrics, and voice activity statistics.
    Provides real-time quality scoring for adaptive ASR parameter tuning.
    """

    def __init__(self, sr=16000):
        self.sr = sr
        self.quality_history = []
        self.history_size = 30

    def estimate_snr(self, signal: np.ndarray, noise_floor: float) -> float:
        signal_energy = float(np.mean(signal ** 2))
        if noise_floor < 1e-10:
            return 30.0
        snr = 10 * np.log10(signal_energy / (noise_floor + 1e-10) + 1e-10)
        return float(np.clip(snr, -10, 50))

    def compute_clipping_ratio(self, signal: np.ndarray) -> float:
        clipped = np.sum(np.abs(signal) >= 0.99)
        return float(clipped / len(signal))

    def compute_dynamic_range(self, signal: np.ndarray) -> float:
        max_val = np.max(np.abs(signal))
        min_val = np.percentile(np.abs(signal), 10)
        if min_val < 1e-10:
            return 0.0
        return float(20 * np.log10(max_val / (min_val + 1e-10)))

    def assess_quality(self, signal: np.ndarray, noise_floor: float) -> dict:
        snr = self.estimate_snr(signal, noise_floor)
        clipping = self.compute_clipping_ratio(signal)
        dynamic_range = self.compute_dynamic_range(signal)
        rms = float(np.sqrt(np.mean(signal ** 2)))

        quality_score = self._compute_quality_score(snr, clipping, dynamic_range, rms)

        self.quality_history.append(quality_score)
        if len(self.quality_history) > self.history_size:
            self.quality_history.pop(0)

        avg_quality = float(np.mean(self.quality_history))

        return {
            "snr_db": round(snr, 1),
            "clipping_ratio": round(clipping, 4),
            "dynamic_range_db": round(dynamic_range, 1),
            "rms": round(rms, 5),
            "quality_score": round(quality_score, 2),
            "avg_quality": round(avg_quality, 2),
            "quality_level": self._quality_label(quality_score)
        }

    def _compute_quality_score(self, snr: float, clipping: float, dr: float, rms: float) -> float:
        snr_score = float(np.clip(snr / 30.0, 0, 1)) * 0.4
        clipping_score = float(np.clip(1.0 - clipping * 100, 0, 1)) * 0.3
        dr_score = float(np.clip(dr / 40.0, 0, 1)) * 0.2
        rms_score = float(np.clip(rms * 20, 0, 1)) * 0.1
        return snr_score + clipping_score + dr_score + rms_score

    @staticmethod
    def _quality_label(score: float) -> str:
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        elif score >= 0.2:
            return "Poor"
        else:
            return "Very Poor"
