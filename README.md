# Local Whisper Dictator

A lightweight, privacy-focused voice dictation tool for Windows. It uses OpenAI's Whisper model (via `faster-whisper`) to provide high-quality, local-only speech-to-text that types directly into any active application.

## 🚀 Features

- **Local Processing**: Your voice never leaves your machine. Privacy by design.
- **System-Wide Dictation**: Works in any text field, word processor, or browser.
- **Interactive Tray Icon**: Visual feedback for Idle, Listening, and Transcribing states.
- **Faster-Whisper**: Optimized for CPU performance using `tiny.en` model and `int8` quantization.

## 🛠️ Prerequisites (windows)

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

## 🛠️ Prerequisites (Linux/Fedora)
Before installing, ensure your system has the necessary development headers and audio libraries.

    Install System Dependencies:
    bash

    sudo dnf install python3.14-devel gcc gcc-c++ portaudio-devel ffmpeg libX11-devel libXtst-devel

    Use code with caution.
    Note: If you are using a different Python version, replace python3.14-devel with your specific version (e.g., python3.13-devel).
    Add User to Input Group:
    To allow the app to read global hotkeys, your user needs permission to access input devices.
    bash

    sudo usermod -aG input $USER

    Use code with caution.
    Important: You must log out and log back in for this change to take effect.

🚀 Installation

    Clone the Repository:
    bash

    git clone https://github.com
    cd voice2code

    Use code with caution.
    Create a Virtual Environment (Recommended):
    bash

    python3.14 -m venv venv
    source venv/bin/activate

    Use code with caution.
    Install Python Packages:
    bash

    pip install faster-whisper pynput pystray sounddevice numpy Pillow evdev

    Use code with caution.

📖 Usage

    Start the Application:
    bash

    python main.py

    Use code with caution.
    Dictate:
        Hold Alt + 0. The tray icon will turn Red.
        Speak your text.
        Release the keys. The icon turns Blue while processing and then types the text into your focused window.

⚠️ Linux Specific Notes (Wayland vs Xorg)

    Xorg (Recommended): This application works best on Xorg. If your hotkeys or typing aren't working, select "GNOME on Xorg" at the Fedora login screen.
    Wayland: Due to security restrictions in the Wayland protocol, global key-listening and "typing" into other windows are often blocked. If you must use Wayland, you may need to run the script with sudo to access /dev/input/ directly.

🔧 Troubleshooting
Issue	Solution
Python.h not found	Run sudo dnf install python3.14-devel.
Hotkey not detected	Ensure you are in the input group and using an Xorg session.
No audio recorded	Verify your default input device in Settings > Sound.
evdev build error	Ensure gcc and python3-devel are installed.

## ⚙️ Configuration

You can easily modify `local_whisper_dictator.py` to change:

- `HOTKEY_COMBINATION`: Change the key combo (e.g., `Ctrl + Shift`).
- `MODEL_NAME`: Use a larger model like `base.en` for better accuracy if your CPU can handle it.
- `INPUT_DEVICE_INDEX`: Set specific microphone index.

## 📄 License

MIT
