# Local Whisper Dictator

A lightweight, privacy-focused voice dictation tool for Windows. It uses OpenAI's Whisper model (via `faster-whisper`) to provide high-quality, local-only speech-to-text that types directly into any active application.

## 🚀 Features

- **Local Processing**: Your voice never leaves your machine. Privacy by design.
- **System-Wide Dictation**: Works in any text field, word processor, or browser.
- **Interactive Tray Icon**: Visual feedback for Idle, Listening, and Transcribing states.
- **Faster-Whisper**: Optimized for CPU performance using `tiny.en` model and `int8` quantization.

## 🛠️ Prerequisites

- **Python 3.8+**
- **FFmpeg**: Required by `faster-whisper`.
- **Microphone**: A working audio input device.

## 📦 Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/local-whisper-dictator.git
   cd local-whisper-dictator
   ```

2. **Install dependencies**:

   ```bash
   pip install faster-whisper pynput pystray Pillow numpy sounddevice
   ```

3. **Audio Setup**:
   The script is currently configured to use your system's default microphone (often Index 1). To check your device indices, you can run:
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```

## ⌨️ Usage

1. Run the script:
   ```bash
   python local_whisper_dictator.py
   ```
2. Wait for the tray icon (green circle) to appear.
3. **Press and hold `Alt + 0`** (Left or Right Alt) to start recording.
4. Speak your dictation.
5. **Release the keys** to start transcription.
6. The transcribed text will be automatically typed into your active window.

## ⚙️ Configuration

You can easily modify `local_whisper_dictator.py` to change:

- `HOTKEY_COMBINATION`: Change the key combo (e.g., `Ctrl + Shift`).
- `MODEL_NAME`: Use a larger model like `base.en` for better accuracy if your CPU can handle it.
- `INPUT_DEVICE_INDEX`: Set specific microphone index.

## 📄 License

MIT
