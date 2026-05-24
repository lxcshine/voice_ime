# -*- coding: utf-8 -*-
try:
    import sounddevice
    print('sounddevice: installed')
except ImportError:
    print('sounddevice: NOT installed')

try:
    import silero_vad
    print('silero_vad: installed')
except ImportError:
    print('silero_vad: NOT installed')

try:
    import funasr
    print('funasr: installed')
except ImportError:
    print('funasr: NOT installed')

try:
    import noisereduce
    print('noisereduce: installed')
except ImportError:
    print('noisereduce: NOT installed')

try:
    import pyperclip
    print('pyperclip: installed')
except ImportError:
    print('pyperclip: NOT installed')

try:
    import pynput
    print('pynput: installed')
except ImportError:
    print('pynput: NOT installed')

try:
    import numpy
    print('numpy: installed')
except ImportError:
    print('numpy: NOT installed')
