# -*- coding: utf-8 -*-
import sounddevice as sd
import numpy as np
import time

print("=" * 50)
print("VoiceIME Microphone Diagnostic Tool")
print("=" * 50)

# 1. List all audio devices
print("\nAvailable audio devices:")
devices = sd.query_devices()
print(devices)

# 2. Find default input device
print("\n" + "=" * 50)
print("Default input device info:")
try:
    default_input = sd.query_devices(kind='input')
    print(f"Device name: {default_input['name']}")
    print(f"Max input channels: {default_input['max_input_channels']}")
    print(f"Default sample rate: {default_input['default_samplerate']}")
except Exception as e:
    print(f"ERROR: No default input device found: {e}")

# 3. Test microphone recording
print("\n" + "=" * 50)
print("Testing microphone (5 seconds recording)...")
print("Please speak into the microphone, volume stats will be shown after test")

try:
    # Use default sample rate
    sr = 16000
    duration = 5  # seconds
    
    recording = sd.rec(
        int(duration * sr),
        samplerate=sr,
        channels=1,
        dtype='float32'
    )
    
    print("Recording...")
    sd.wait()
    print("Recording complete!")
    
    # Analyze recording
    volume_levels = np.abs(recording)
    avg_volume = float(np.mean(volume_levels))
    max_volume = float(np.max(volume_levels))
    
    print(f"\nRecording analysis:")
    print(f"Average volume: {avg_volume:.6f}")
    print(f"Max volume: {max_volume:.6f}")
    print(f"Recording length: {len(recording)} samples ({len(recording)/sr:.2f} seconds)")
    
    if avg_volume < 0.001:
        print("\nWARNING: Volume is very low, may not have detected sound")
        print("Possible reasons:")
        print("1. Microphone not connected or disabled")
        print("2. Microphone volume set too low")
        print("3. Wrong input device selected")
    elif avg_volume < 0.01:
        print("\nNOTE: Volume is low, please ensure microphone is working properly")
    else:
        print("\nSUCCESS: Microphone is working normally and can detect sound!")
        
except Exception as e:
    print(f"\nERROR: Recording test failed: {e}")
    print("\nPossible reasons:")
    print("1. No available microphone device")
    print("2. Microphone permission denied")
    print("3. sounddevice library configuration issue")

print("\n" + "=" * 50)
print("Diagnostic complete!")
print("=" * 50)
