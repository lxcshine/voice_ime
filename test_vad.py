# -*- coding: utf-8 -*-
import sounddevice as sd
import numpy as np
import time
import torch
from silero_vad import load_silero_vad

print("=" * 60)
print("VAD (Voice Activity Detection) Test")
print("=" * 60)

sr = 16000
chunk_size = int(sr * 0.03)  # 30ms
threshold = 0.5  # VAD threshold

print(f"\nSample rate: {sr}")
print(f"Chunk size: {chunk_size} samples (30ms)")
print(f"VAD threshold: {threshold}")

print("\nLoading Silero VAD model...")
vad_model = load_silero_vad()
print("VAD model loaded")

print("\n" + "=" * 60)
print("Testing VAD for 10 seconds...")
print("Please speak loudly and watch VAD detection!")
print("=" * 60 + "\n")

speech_count = 0
total_count = 0

def callback(indata, frames, time_info, status):
    global speech_count, total_count
    
    if status:
        print(f"Status: {status}")
    
    # Get audio chunk
    data = indata[:, 0].astype(np.float32)
    volume = float(np.abs(data).mean())
    
    # VAD processing
    tensor = torch.from_numpy(data).float()
    if len(tensor) < 512:
        tensor = torch.nn.functional.pad(tensor, (0, 512 - len(tensor)))
    
    try:
        speech_prob = vad_model(tensor, sr).item()
        is_speech = speech_prob > threshold
        
        total_count += 1
        if is_speech:
            speech_count += 1
        
        # Display results using ASCII only
        bar_length = int(min(volume * 50, 30))
        bar = "#" * bar_length + "-" * (30 - bar_length)
        
        if is_speech:
            vad_status = "[SPEECH]"
        else:
            vad_status = "[silent]"
        print(f"{vad_status} Vol: {volume:.5f} | VAD: {speech_prob:.3f} | {bar}")
    except Exception as e:
        print(f"VAD error: {e}")

try:
    with sd.InputStream(
        samplerate=sr,
        channels=1,
        dtype='float32',
        blocksize=chunk_size,
        callback=callback
    ):
        print("\nMicrophone stream started\n")
        time.sleep(10)
        
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("VAD Test Summary:")
print("=" * 60)
print(f"Total chunks: {total_count}")
print(f"Speech detected: {speech_count}/{total_count}")
if total_count > 0:
    speech_percent = (speech_count / total_count) * 100
    print(f"Speech percentage: {speech_percent:.1f}%")
    
    if speech_count > 0:
        print("\nVAD is working! It detected your speech.")
        print("   If VoiceIME is not responding, the issue might be:")
        print("   1. Hotkey not configured correctly")
        print("   2. ASR model not loaded properly")
        print("   3. Scheduler not starting recording")
    else:
        print("\nVAD did not detect any speech.")
        print("   Try speaking louder or lowering the VAD_THRESHOLD in .env file")
