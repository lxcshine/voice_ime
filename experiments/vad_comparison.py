import numpy as np
import time
from core.adaptive_vad import AdaptiveVADController
from core.audio_features import AudioFeatureExtractor, SpeechQualityAssessor
from utils.logger import logger


def generate_test_audio(sr=16000, duration=30, snr_db=10):
    """Generate synthetic audio with speech-like segments and noise."""
    total_samples = sr * duration
    audio = np.zeros(total_samples, dtype=np.float32)

    noise_power = 0.01
    speech_power = noise_power * (10 ** (snr_db / 10))

    noise = np.random.randn(total_samples).astype(np.float32) * np.sqrt(noise_power)
    audio += noise

    speech_segments = [
        (2, 5), (7, 10), (12, 15), (17, 20), (22, 25), (27, 29)
    ]

    for start, end in speech_segments:
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        t = np.linspace(0, end - start, end_sample - start_sample)

        speech = (
            0.5 * np.sin(2 * np.pi * 200 * t) +
            0.3 * np.sin(2 * np.pi * 400 * t) +
            0.2 * np.sin(2 * np.pi * 800 * t)
        )
        speech *= np.sqrt(speech_power / (np.mean(speech ** 2) + 1e-10))

        envelope = np.ones(len(speech))
        fade_len = int(0.1 * sr)
        if fade_len < len(envelope) // 2:
            envelope[:fade_len] = np.linspace(0, 1, fade_len)
            envelope[-fade_len:] = np.linspace(1, 0, fade_len)

        audio[start_sample:end_sample] += speech * envelope

    return audio, speech_segments


def evaluate_vad(vad_controller, audio, sr=16000, frame_size=512, speech_segments=None):
    """Evaluate VAD performance on audio data."""
    num_frames = len(audio) // frame_size
    frame_duration = frame_size / sr

    detections = []
    is_speaking = False
    speech_start = None

    for i in range(num_frames):
        start = i * frame_size
        end = start + frame_size
        frame = audio[start:end]

        res = vad_controller.process(frame)

        if res.get("is_end"):
            if speech_start is not None:
                detections.append((speech_start, i * frame_duration))
            speech_start = None
            is_speaking = False
        elif res.get("speech_prob", 0) > res.get("threshold", 0.5):
            if not is_speaking:
                speech_start = i * frame_duration
                is_speaking = True
        else:
            if is_speaking:
                silence_samples = (i * frame_size) - (speech_start * sr if speech_start else 0)
                if silence_samples > int(0.6 * sr):
                    if speech_start is not None:
                        detections.append((speech_start, i * frame_duration))
                    speech_start = None
                    is_speaking = False

    if is_speaking and speech_start is not None:
        detections.append((speech_start, num_frames * frame_duration))

    if speech_segments:
        tp = 0
        fp = 0
        fn = 0

        for det_start, det_end in detections:
            det_mid = (det_start + det_end) / 2
            matched = False
            for seg_start, seg_end in speech_segments:
                seg_mid = (seg_start + seg_end) / 2
                if abs(det_mid - seg_mid) < 1.0:
                    tp += 1
                    matched = True
                    break
            if not matched:
                fp += 1

        fn = len(speech_segments) - tp

        precision = tp / (tp + fp + 1e-10)
        recall = tp / (tp + fn + 1e-10)
        f1 = 2 * precision * recall / (precision + recall + 1e-10)

        return {
            "detections": len(detections),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

    return {"detections": len(detections)}


def run_comparison():
    """Run comparison between fixed and adaptive VAD thresholds."""
    print("=" * 60)
    print("VAD Performance Comparison: Fixed vs Adaptive Threshold")
    print("=" * 60)

    snr_levels = [0, 5, 10, 15, 20, 25]
    results = {"fixed": [], "adaptive": []}

    for snr in snr_levels:
        print(f"\nTesting SNR = {snr} dB...")

        audio, speech_segments = generate_test_audio(snr_db=snr)

        fixed_vad = AdaptiveVADController(use_adaptive=False)
        fixed_results = evaluate_vad(fixed_vad, audio, speech_segments=speech_segments)
        results["fixed"].append(fixed_results)

        adaptive_vad = AdaptiveVADController(use_adaptive=True)
        adaptive_results = evaluate_vad(adaptive_vad, audio, speech_segments=speech_segments)
        results["adaptive"].append(adaptive_results)

        print(f"  Fixed:    F1={fixed_results['f1_score']:.3f}, "
              f"P={fixed_results['precision']:.3f}, R={fixed_results['recall']:.3f}")
        print(f"  Adaptive: F1={adaptive_results['f1_score']:.3f}, "
              f"P={adaptive_results['precision']:.3f}, R={adaptive_results['recall']:.3f}")

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"{'SNR (dB)':<10} {'Fixed F1':<12} {'Adaptive F1':<12} {'Improvement':<12}")
    print("-" * 60)

    for i, snr in enumerate(snr_levels):
        fixed_f1 = results["fixed"][i]["f1_score"]
        adaptive_f1 = results["adaptive"][i]["f1_score"]
        improvement = adaptive_f1 - fixed_f1
        print(f"{snr:<10} {fixed_f1:<12.3f} {adaptive_f1:<12.3f} {improvement:+.3f}")

    avg_fixed = np.mean([r["f1_score"] for r in results["fixed"]])
    avg_adaptive = np.mean([r["f1_score"] for r in results["adaptive"]])
    print("-" * 60)
    print(f"{'Average':<10} {avg_fixed:<12.3f} {avg_adaptive:<12.3f} {avg_adaptive - avg_fixed:+.3f}")

    return results


if __name__ == "__main__":
    run_comparison()
