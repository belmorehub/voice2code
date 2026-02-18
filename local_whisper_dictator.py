
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

# --- Configuration ---
HOTKEY_KEY = keyboard.Key.alt_r  # Hotkey to hold for dictation
MODEL_NAME = "tiny.en"  # Optimized for CPU, consider "base.en" for better accuracy if tiny.en is insufficient
SAMPLERATE = 16000  # Whisper model expects 16kHz audio
CHUNK_SIZE = 1024
CHANNELS = 1
DTYPE = 'int16'
INPUT_DEVICE_INDEX = 1 # Explicitly set to your "Headset (HD 450BT)" input device

# Path for faster-whisper cache
APP_DIR = os.path.join(os.path.expanduser("~"), ".local_whisper_dictator")
os.makedirs(APP_DIR, exist_ok=True)
MODEL_CACHE_DIR = os.path.join(APP_DIR, "models")
os.makedirs(MODEL_CACHE_DIR, exist_ok=True)


# --- Globals ---
audio_buffer = queue.Queue()
is_recording = False
model = None
icon = None
current_audio_data = [] # Stores audio chunks for the current recording session
audio_stream = None # Declare audio_stream globally and initialize later

IDLE_ICON = None
LISTENING_ICON = None
TRANSCRIBING_ICON = None

# --- Audio Recording ---
def audio_callback(indata, frames, time_info, status):
    """This is called (in a separate thread) for each audio block."""
    global current_audio_data
    if status:
        print(f"Audio callback status: {status}", flush=True)
    if is_recording:
        # Append the numpy array directly
        current_audio_data.append(indata.copy())

def start_recording():
    global is_recording, current_audio_data, audio_stream
    if not is_recording:
        print("Starting recording...", flush=True)
        is_recording = True
        current_audio_data = [] # Clear previous audio for a new recording
        if icon:
            icon.icon = LISTENING_ICON
            icon.title = 'Local Whisper Dictator - LISTENING'
        
        try:
            # Start the audio stream
            audio_stream = sd.InputStream(
                samplerate=SAMPLERATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE,
                callback=audio_callback,
                device=INPUT_DEVICE_INDEX # Use the specified input device
            )
            audio_stream.start()
        except Exception as e:
            print(f"Error starting audio stream: {e}", flush=True)
            is_recording = False # Reset flag if stream fails to start

def stop_recording_and_transcribe():
    global is_recording, audio_stream
    if is_recording:
        print("Stopping recording...", flush=True)
        is_recording = False
        if audio_stream and audio_stream.stopped == False:
            audio_stream.stop()
            audio_stream.close()
        
        if icon:
            icon.icon = TRANSCRIBING_ICON
            icon.title = 'Local Whisper Dictator - TRANSCRIBING'
        
        # Process the buffered audio data in a new thread to avoid blocking hotkey listener
        threading.Thread(target=process_audio_for_transcription).start()

def process_audio_for_transcription():
    global current_audio_data
    print("Processing audio for transcription...", flush=True)
    if not current_audio_data:
        print("No audio data to transcribe.", flush=True)
        return

    # Concatenate all numpy arrays from the buffer
    # Ensure that current_audio_data contains items before concatenating
    if current_audio_data:
        recorded_audio = np.concatenate(current_audio_data, axis=0)
    else:
        print("No audio data collected during recording.", flush=True)
        return

    # Convert to float32 as expected by faster-whisper
    # sounddevice returns int16, Whisper expects float32 in range [-1, 1]
    recorded_audio_float32 = recorded_audio.astype(np.float32) / 32768.0

    print("Transcribing audio...", flush=True)
    try:
        segments, info = model.transcribe(
            recorded_audio_float32,
            beam_size=5,
            vad_filter=True, # Use voice activity detection
            vad_parameters=dict(min_silence_duration_ms=500) # Optional: adjust VAD sensitivity
        )

        full_text = []
        for segment in segments:
            full_text.append(segment.text)
        
        transcribed_text = " ".join(full_text).strip()
        print(f"Transcribed: '{transcribed_text}'", flush=True)

        if transcribed_text:
            # Simulate typing the text
            type_text(transcribed_text)
    except Exception as e:
        print(f"Error during transcription: {e}", flush=True)
    finally: # Ensure icon reverts to idle state even if transcription fails
        if icon:
            icon.icon = IDLE_ICON
            icon.title = 'Local Whisper Dictator (Hotkey: Right Alt)'

# --- Keyboard Input Simulation ---
def type_text(text):
    print(f"Typing: '{text}'", flush=True)
    controller = keyboard.Controller()
    # It's often better to paste for longer texts, but for short dictation, typing is fine.
    # For now, let's stick to typing.
    for char in text:
        controller.press(char)
        controller.release(char)
        # A very small delay can help with some applications
        time.sleep(0.005) # Reduced delay

# --- Hotkey Listener ---
def on_press(key):
    # Only act if the hotkey is the one we're looking for
    # and if we are not already recording
    if key == HOTKEY_KEY:
        start_recording()

def on_release(key):
    # Only act if the hotkey is the one we're looking for
    # and if we are currently recording
    if key == HOTKEY_KEY:
        stop_recording_and_transcribe()

# --- System Tray Icon ---
def create_icon_images():
    global IDLE_ICON, LISTENING_ICON, TRANSCRIBING_ICON
    # Load or create images
    try:
        # Attempt to load a base icon and tint it
        base_image_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(base_image_path):
            base_image = Image.open(base_image_path).resize((64, 64))
        else:
            print("icon.png not found, creating a default transparent base image.", flush=True)
            base_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0)) # Fully transparent base
        
        # Create different state icons by drawing colored circles on the base
        IDLE_ICON = base_image.copy()
        draw = ImageDraw.Draw(IDLE_ICON)
        draw.ellipse((16, 16, 48, 48), fill=(60, 179, 113)) # Green for Idle

        LISTENING_ICON = base_image.copy()
        draw = ImageDraw.Draw(LISTENING_ICON)
        draw.ellipse((16, 16, 48, 48), fill=(255, 0, 0)) # Red for Listening

        TRANSCRIBING_ICON = base_image.copy()
        draw = ImageDraw.Draw(TRANSCRIBING_ICON)
        draw.ellipse((16, 16, 48, 48), fill=(0, 0, 255)) # Blue for Transcribing

    except Exception as e:
        print(f"Error creating icon images: {e}. Falling back to simple colored squares.", flush=True)
        # Fallback to generated simple colored squares if drawing fails
        IDLE_ICON = Image.new('RGB', (64, 64), (60, 179, 113)) # Green
        LISTENING_ICON = Image.new('RGB', (64, 64), (255, 0, 0)) # Red
        TRANSCRIBING_ICON = Image.new('RGB', (64, 64), (0, 0, 255)) # Blue

def setup_icon():
    global icon
    create_icon_images() # Create icon images before setting up the icon

    icon = Icon(
        'LocalWhisperDictator',
        IDLE_ICON, # Start with idle icon
        'Local Whisper Dictator (Hotkey: Right Alt)',
        menu=Menu(
            MenuItem('Exit', lambda icon, item: on_exit(icon))
        )
    )
    icon.run() # This call blocks until the icon is exited

def on_exit(icon_instance):
    print("Exiting application...", flush=True)
    icon_instance.stop()
    # Ensure all threads are stopped gracefully if necessary
    os._exit(0) # Force exit all threads

# --- Main Application Loop ---
def main():
    global model
    print(f"Local Whisper Dictator starting...", flush=True)
    print(f"Loading Whisper model '{MODEL_NAME}' from cache '{MODEL_CACHE_DIR}'...", flush=True)
    # Load model once at startup
    # compute_type="int8" is good for CPU performance
    model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8", download_root=MODEL_CACHE_DIR)
    print("Model loaded successfully.", flush=True)

    # Start hotkey listener in a separate thread, as it needs to run continuously
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    print(f"Hotkey listener started. Use '{HOTKEY_KEY.name}' to dictate.", flush=True)

    # Start system tray icon (this will block the main thread)
    setup_icon()

    # The program flow will essentially be handled by the hotkey listener and the tray icon.
    # The listener thread will run in the background, and setup_icon() blocks until exit.
    listener.join() # This line might not be reached if on_exit calls os._exit(0)

if __name__ == "__main__":
    main()
