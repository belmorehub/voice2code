import sounddevice as sd
import numpy as np
import threading
import time
import queue
import io
import os
from faster_whisper import WhisperModel
from pynput import keyboard, mouse
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

HOTKEY_COMBINATION = {keyboard.Key.alt_l, keyboard.KeyCode.from_char('0')}
MODEL_NAME = "tiny.en"
SAMPLERATE = 16000
CHUNK_SIZE = 1024
CHANNELS = 1
DTYPE = 'int16'
INPUT_DEVICE_INDEX = 1

APP_DIR = os.path.join(os.path.expanduser("~"), ".local_whisper_dictator")
os.makedirs(APP_DIR, exist_ok=True)
MODEL_CACHE_DIR = os.path.join(APP_DIR, "models")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

audio_buffer = queue.Queue()
is_recording = False
model = None
icon = None
current_audio_data = []
audio_stream = None
pressed_keys = set()

IDLE_ICON = None
LISTENING_ICON = None
TRANSCRIBING_ICON = None

def audio_callback(indata, frames, time_info, status):
    global current_audio_data
    if status:
        print(f"Audio callback status: {status}", flush=True)
    if is_recording:
        current_audio_data.append(indata.copy())

def start_recording():
    global is_recording, current_audio_data, audio_stream
    if not is_recording:
        print("Starting recording...", flush=True)
        is_recording = True
        current_audio_data = []
        if icon:
            try:
                icon.icon = LISTENING_ICON
                icon.title = 'Local Whisper Dictator - LISTENING'
            except Exception as e:
                print(f"Error updating icon to Listening: {e}", flush=True)
        
        try:
            audio_stream = sd.InputStream(
                samplerate=SAMPLERATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE,
                callback=audio_callback,
                device=INPUT_DEVICE_INDEX
            )
            audio_stream.start()
        except Exception as e:
            print(f"Error starting audio stream: {e}", flush=True)
            is_recording = False

def stop_recording_and_transcribe():
    global is_recording, audio_stream
    if is_recording:
        print("Stopping recording...", flush=True)
        is_recording = False
        if audio_stream and audio_stream.stopped == False:
            audio_stream.stop()
            audio_stream.close()
        
        if icon:
            try:
                icon.icon = TRANSCRIBING_ICON
                icon.title = 'Local Whisper Dictator - TRANSCRIBING'
            except Exception as e:
                print(f"Error updating icon to Transcribing: {e}", flush=True)
        
        threading.Thread(target=process_audio_for_transcription).start()

def process_audio_for_transcription():
    global current_audio_data
    print("Processing audio for transcription...", flush=True)
    if not current_audio_data:
        print("No audio data to transcribe.", flush=True)
        return

    if current_audio_data:
        recorded_audio = np.concatenate(current_audio_data, axis=0)
    else:
        print("No audio data collected during recording.", flush=True)
        return

    recorded_audio_float32 = recorded_audio.flatten().astype(np.float32) / 32768.0

    print("Transcribing audio...", flush=True)
    try:
        segments, info = model.transcribe(
            recorded_audio_float32,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        full_text = []
        for segment in segments:
            full_text.append(segment.text)
        
        transcribed_text = " ".join(full_text).strip()
        print(f"Transcribed: '{transcribed_text}'", flush=True)

        if transcribed_text:
            type_text(transcribed_text)
    except Exception as e:
        print(f"Error during transcription: {e}", flush=True)
    finally:
        if icon:
            try:
                icon.icon = IDLE_ICON
                icon.title = 'Local Whisper Dictator (Hotkey: Alt + 0)'
            except Exception as e:
                print(f"Error updating icon to Idle: {e}", flush=True)

def type_text(text):
    print(f"Typing: '{text}'", flush=True)
    controller = keyboard.Controller()
    for char in text:
        try:
            controller.press(char)
            controller.release(char)
        except Exception as e:
            print(f"Error typing char '{char}': {e}", flush=True)
        time.sleep(0.005)

def on_press(key):
    global pressed_keys
    if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
        pressed_keys.add(keyboard.Key.alt_l)
    elif hasattr(key, 'char') and key.char == '0':
        pressed_keys.add(keyboard.KeyCode.from_char('0'))
    
    if keyboard.Key.alt_l in pressed_keys and keyboard.KeyCode.from_char('0') in pressed_keys:
        if not is_recording:
            print("Hotkey Alt + 0 DETECTED! Starting recording...", flush=True)
            start_recording()

def on_release(key):
    global pressed_keys
    was_recording = is_recording
    is_hotkey_key = False
    if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
        if keyboard.Key.alt_l in pressed_keys:
            pressed_keys.remove(keyboard.Key.alt_l)
        is_hotkey_key = True
    elif hasattr(key, 'char') and key.char == '0':
        key_code = keyboard.KeyCode.from_char('0')
        if key_code in pressed_keys:
            pressed_keys.remove(key_code)
        is_hotkey_key = True
    
    if was_recording and is_hotkey_key:
        print("Hotkey released. Stopping recording...", flush=True)
        stop_recording_and_transcribe()

def create_icon_images():
    global IDLE_ICON, LISTENING_ICON, TRANSCRIBING_ICON
    try:
        base_image_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(base_image_path):
            base_image = Image.open(base_image_path).resize((64, 64))
        else:
            print("icon.png not found, creating a default transparent base image.", flush=True)
            base_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        
        IDLE_ICON = base_image.copy()
        draw = ImageDraw.Draw(IDLE_ICON)
        draw.ellipse((16, 16, 48, 48), fill=(60, 179, 113))

        LISTENING_ICON = base_image.copy()
        draw = ImageDraw.Draw(LISTENING_ICON)
        draw.ellipse((16, 16, 48, 48), fill=(255, 0, 0))

        TRANSCRIBING_ICON = base_image.copy()
        draw = ImageDraw.Draw(TRANSCRIBING_ICON)
        draw.ellipse((16, 16, 48, 48), fill=(0, 0, 255))

    except Exception as e:
        print(f"Error creating icon images: {e}. Falling back to simple colored squares.", flush=True)
        IDLE_ICON = Image.new('RGB', (64, 64), (60, 179, 113))
        LISTENING_ICON = Image.new('RGB', (64, 64), (255, 0, 0))
        TRANSCRIBING_ICON = Image.new('RGB', (64, 64), (0, 0, 255))

def setup_icon():
    global icon
    create_icon_images()
    icon = Icon(
        'LocalWhisperDictator',
        IDLE_ICON,
        'Local Whisper Dictator (Hotkey: Alt + 0)',
        menu=Menu(
            MenuItem('Exit', lambda icon, item: on_exit(icon))
        )
    )
    icon.run()

def on_exit(icon_instance):
    print("Exiting application...", flush=True)
    icon_instance.stop()
    os._exit(0)

def main():
    global model
    print(f"Local Whisper Dictator starting...", flush=True)
    print(f"Loading Whisper model '{MODEL_NAME}' from cache '{MODEL_CACHE_DIR}'...", flush=True)
    model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8", download_root=MODEL_CACHE_DIR)
    print("Model loaded successfully.", flush=True)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    print(f"Hotkey listener started. Use 'Alt + 0' to dictate.", flush=True)

    setup_icon()
    listener.join()

if __name__ == "__main__":
    main()
