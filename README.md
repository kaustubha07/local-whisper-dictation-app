# 🎙️ Local Whisper Dictation App

A production-ready, local-first desktop dictation application that transcribes speech into text and injects it at your cursor in **any** application.

## High-Performance, Privacy-First Features
- **Fully Local Inference:** Runs Faster-Whisper entirely on your machine. No cloud, no APIs, no internet required.
- **Smart Voice Detection:** Uses Silero VAD to intelligently separate speech from background noise.
- **System-Wide Integration:** Works across VS Code, Word, Browser, Notch, and any other text-input field.
- **Premium UI:** Features a sleek system tray icon and a minimalist "glass-style" status overlay.
- **Secure Injection:** Uses clipboard-based text insertion to ensure unicode safety and cross-app compatibility.

## 🚀 Getting Started

### Prerequisites
- **Python 3.9+**
- **Windows / macOS / Linux**
- **FFmpeg** (Recommended for audio processing)

### Installation
1.  **Clone and Install:**
    ```bash
    git clone [your-repo-url]
    cd dictation-app
    pip install -r requirements.txt
    ```

2.  **Platform-Specific dependencies:**
    - **Linux:** `sudo apt install xclip portaudio19-dev`
    - **macOS:** `brew install portaudio`

3.  **Run:**
    ```bash
    python main.py
    ```

### ⌨️ Default Hotkeys
- **`Ctrl + Alt + Space`**: Toggle Recording (Start/Stop)

## ⚙️ Configuration
The app creates a configuration file at `~/.dictation-app/config.json` on the first run. You can also access settings via the **System Tray Menu**.

- **Model size:** `tiny`, `base` (default), `small`, `medium`
- **Device:** `cpu` or `cuda`
- **Hotkey:** Customizable `pynput` format.

## 🛠️ Project Structure
```text
dictation-app/
├── main.py            # Orchestrator & Hotkeys
├── engine/
│   ├── recorder.py    # Audio & VAD
│   ├── transcriber.py # Faster-Whisper
│   └── injector.py    # Text Injection
├── ui/
│   ├── tray.py        # System Tray & Settings
│   └── overlay.py     # Status Overlay
└── config.py          # Settings Persistence
```

## 📜 License
MIT License
