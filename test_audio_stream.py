# -*- coding: utf-8 -*-
import sounddevice as sd
import numpy as np
import time

print("=" * 60)
print("Real-time Audio Monitor for VoiceIME")
print("=" * 60)

sr = 16000
chunk_size = int(sr * 0.03)  # 30ms

print(f"\nSample rate: {sr}")
print(f"Chunk size: {chunk_size} samples (30ms)")
print(f"\nDefault input device:")
default_input = sd.query_devices(kind='input')
print(f"  Name: {default_input['name']}")
print(f"  Channels: {default_input['max_input_channels']}")
print(f"  Sample rate: {default_input['default_samplerate']}")

print("\n" + "=" * 60)
print("Monitoring audio stream (10 seconds)...")
print("Please speak loudly and watch the volume levels change!")
print("=" * 60 + "\n")

volume_history = []

def callback(indata, frames, time_info, status):
    if status:
        print(f"Status: {status}")
    
    # Calculate volume
    data = indata[:, 0].astype(np.float32)
    volume = float(np.abs(data).mean())
    max_vol = float(np.abs(data).max())
    
    volume_history.append(volume)
    
    # Display volume bar using ASCII only
    bar_length = int(min(volume * 50, 30))
    bar = "#" * bar_length + "-" * (30 - bar_length)
    
    # Detect if speech is present (threshold 0.01)
    if volume > 0.01:
        speech_indicator = "[SPEECH]"
    else:
        speech_indicator = "[silent]"
    
    print(f"{speech_indicator} Avg: {volume:.5f} | Max: {max_vol:.5f} | {bar}")

try:
    # Record for 10 seconds
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
print("Summary:")
print("=" * 60)

if volume_history:
    avg_volume = np.mean(volume_history)
    max_volume = np.max(volume_history)
    speech_chunks = sum(1 for v in volume_history if v > 0.01)
    speech_percent = (speech_chunks / len(volume_history)) * 100
    
    print(f"Total chunks: {len(volume_history)}")
    print(f"Average volume: {avg_volume:.5f}")
    print(f"Max volume: {max_volume:.5f}")
    print(f"Speech detected: {speech_chunks}/{len(volume_history)} ({speech_percent:.1f}%)")
    
    if max_volume > 0.1:
        print("\nGOOD: Microphone is working well!")
        print("   Your voice is being captured clearly.")
    elif max_volume > 0.01:
        print("\nLOW: Microphone works but volume is low")
        print("   Try speaking louder or check system microphone settings.")
    else:
        print("\nPROBLEM: Very low volume detected")
        print("   Check if microphone is enabled and not muted.")
