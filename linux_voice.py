import sounddevice as sd
import numpy as np
import threading
import time
import queue
import os
import sys
from faster_whisper import WhisperModel
from pynput import keyboard
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

# --- CONFIGURATION ---
MODEL_NAME = "tiny.en"
SAMPLERATE = 16000
CHUNK_SIZE = 1024
CHANNELS = 1
DTYPE = 'int16'

# Fedora/Linux Directory Standard
APP_DIR = os.path.join(os.path.expanduser("~"), ".local/share/whisper_dictator")
os.makedirs(APP_DIR, exist_ok=True)
MODEL_CACHE_DIR = os.path.join(APP_DIR, "models")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

# Global States
audio_buffer = queue.Queue()
is_recording = False
model = None
icon = None
current_audio_data = []
audio_stream = None
pressed_keys = set()

# Icons
IDLE_ICON = None
LISTENING_ICON = None
TRANSCRIBING_ICON = None

def get_default_input_device():
    """Finds the default input device index on Fedora/PulseAudio/Pipewire."""
    try:
        device_info = sd.query_devices(kind='input')
        return device_info['index']
    except Exception:
        return None

def audio_callback(indata, frames, time_info, status):
    if status:
        print(f"Audio status: {status}", file=sys.stderr)
    if is_recording:
        current_audio_data.append(indata.copy())

def start_recording():
    global is_recording, current_audio_data, audio_stream
    if not is_recording:
        print(">> Listening...", flush=True)
        is_recording = True
        current_audio_data = []
        update_icon(LISTENING_ICON, 'Listening...')
        
        try:
            audio_stream = sd.InputStream(
                samplerate=SAMPLERATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE,
                callback=audio_callback,
                device=get_default_input_device()
            )
            audio_stream.start()
        except Exception as e:
            print(f"Audio Error: {e}")
            is_recording = False

def stop_recording_and_transcribe():
    global is_recording, audio_stream
    if is_recording:
        is_recording = False
        if audio_stream:
            audio_stream.stop()
            audio_stream.close()
        
        update_icon(TRANSCRIBING_ICON, 'Transcribing...')
        threading.Thread(target=process_audio_for_transcription, daemon=True).start()

def process_audio_for_transcription():
    global current_audio_data
    if not current_audio_data:
        update_icon(IDLE_ICON, 'Ready')
        return

    recorded_audio = np.concatenate(current_audio_data, axis=0)
    audio_fp32 = recorded_audio.flatten().astype(np.float32) / 32768.0

    try:
        segments, _ = model.transcribe(audio_fp32, beam_size=5, vad_filter=True)
        text = " ".join([s.text for s in segments]).strip()
        
        if text:
            print(f"Result: {text}")
            type_text(text)
    except Exception as e:
        print(f"Transcription Error: {e}")
    finally:
        update_icon(IDLE_ICON, 'Alt + 0 to Dictate')

def type_text(text):
    """Types text via pynput. Best on Xorg."""
    controller = keyboard.Controller()
    # On Linux, sometimes a small delay helps focus return to the app
    time.sleep(0.1) 
    controller.type(text)

def on_press(key):
    # Handle Alt+0 specifically
    if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
        pressed_keys.add('alt')
    elif hasattr(key, 'char') and key.char == '0':
        pressed_keys.add('0')
    
    if 'alt' in pressed_keys and '0' in pressed_keys:
        if not is_recording:
            start_recording()

def on_release(key):
    if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
        if 'alt' in pressed_keys: pressed_keys.remove('alt')
        if is_recording: stop_recording_and_transcribe()
    elif hasattr(key, 'char') and key.char == '0':
        if '0' in pressed_keys: pressed_keys.remove('0')
        if is_recording: stop_recording_and_transcribe()

def update_icon(img, title):
    if icon:
        icon.icon = img
        icon.title = f"Whisper: {title}"

def create_icon_images():
    global IDLE_ICON, LISTENING_ICON, TRANSCRIBING_ICON
    # Create simple colored circles for Fedora top bar
    def make_circle(color):
        img = Image.new('RGBA', (64, 64), (0,0,0,0))
        d = ImageDraw.Draw(img)
        d.ellipse((8, 8, 56, 56), fill=color)
        return img

    IDLE_ICON = make_circle((60, 179, 113)) # Green
    LISTENING_ICON = make_circle((255, 0, 0)) # Red
    TRANSCRIBING_ICON = make_circle((0, 120, 255)) # Blue

def setup_icon():
    global icon
    create_icon_images()
    icon = Icon('WhisperDictator', IDLE_ICON, "Whisper Dictator", 
                menu=Menu(MenuItem('Exit', lambda: os._exit(0))))
    icon.run()

def main():
    global model
    print("Loading Model...")
    # Use CPU/Int8 for compatibility; change to 'cuda' if you have an NVIDIA GPU
    model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8", download_root=MODEL_CACHE_DIR)
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    setup_icon()

if __name__ == "__main__":
    main()
