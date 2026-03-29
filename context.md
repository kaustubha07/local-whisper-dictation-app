# 🎙️ Local Whisper Dictation App - Project Context

This document provides a comprehensive overview of the **Local Whisper Dictation App**, designed for developers and AI coding assistants to understand, contribute to, and improve the codebase.

## 🌟 Project Overview
A production-ready, local-first desktop application for Windows (with cross-platform potential) that provides system-wide speech-to-text dictation. It transcribes audio using **Faster-Whisper** and injects the resulting text directly into the active cursor of any application.

### Key Pillars:
- **Privacy-First:** All processing happens locally. No cloud APIs or internet connection required.
- **Low Latency:** Optimized for speed using `float16`/`int8` quantization and Silero VAD.
- **System-Wide:** Works in any text input field (VS Code, Browser, Word, etc.) via global hotkeys.
- **Context-Aware:** Features "Vocabulary Profiles" and an "App Watcher" that switches context based on the active window.

---

## 🛠️ Technology Stack
- **Language:** Python 3.9+
- **STT Engine:** `faster-whisper` (CTranslate2 backend)
- **VAD (Voice Activity Detection):** `silero-vad` (via `torch`)
- **Audio I/O:** `sounddevice` / `PyAudio`
- **Global Hotkeys:** `keyboard` (for suppression) & `pynput`
- **UI Toolkit:** `tkinter` (Status Overlay) & `pystray` (System Tray)
- **Injection:** `pyperclip` (Clipboard-based injection for maximum compatibility)
- **Backend:** `torch`, `torchaudio`, `numpy`

---

## 🏗️ Core Architecture

### 1. Orchestrator (`main.py`)
- **`DictationApp` Class:** The central hub. Manages the lifecycle of all components.
- **State Management:** Uses an `AppState` dataclass (idle, recording, processing) with thread locks.
- **Asynchronous Execution:** Transcription runs in a `ThreadPoolExecutor` to keep the UI responsive.
- **Hotkey Management:** Handles the registration and toggling logic for system-wide activation.

### 2. Engine Layer (`engine/`)
- **`recorder.py`**: Handles microphone input and real-time Silero VAD filtering. Implements "silence-to-stop" logic.
- **`transcriber.py`**: Encapsulates Faster-Whisper. Handles model loading, quantization (`int8`/`float16`), and inference.
- **`injector.py`**: Manages the "pasting" of transcribed text. Uses a clipboard backup/restore mechanism to avoid data loss.
- **`app_watcher.py`**: Monitors the active window and switches vocabulary profiles (e.g., "Coding" profile for VS Code).
- **`history.py`**: Logs transcriptions for debugging and user reference.

### 3. UI Layer (`ui/`)
- **`overlay.py`**: A minimalist, semi-transparent `tkinter` window that shows current status (Recording, Transcribing, Success/Error).
- **`tray.py`**: System tray icon providing a settings menu, profile selection, and manual controls.

---

## 🔄 Core Workflow (The "Loop")
1. **Listen:** `keyboard` listener waits for the global hotkey (default: `Ctrl+Alt+Space`).
2. **Record:** `AudioRecorder` captures chunks, runs them through Silero VAD.
3. **Detection:** Once speech stops (detected by VAD) or the hotkey is pressed again, recording halts.
4. **Process:** Audio data is sent to `Transcriber`.
5. **Transcribe:** Faster-Whisper generates text using the active profile's `initial_prompt`.
6. **Inject:** `TextInjector` copies text to clipboard -> Sends `Ctrl+V` -> Restores original clipboard.
7. **Feedback:** `StatusOverlay` provides visual confirmation.

---

## ⚙️ Configuration & Profiles
- **Location:** `~/.dictation-app/config.json`
- **Vocabulary Profiles:** Allows users to define "initial prompts" (keywords) for specific domains (Coding, Medical, etc.).
- **App Profiles:** Maps process names (e.g., `code.exe`) to vocabulary profiles.

---

## 💡 Context for LLMs (Helpful Patterns)
- **Thread Safety:** Most UI operations (Tray, Overlay) run in their own threads. Use `root.after()` for `tkinter` updates from background threads.
- **Hotkey Reliability:** The app uses `keyboard.add_hotkey` with `suppress=True` to prevent the hotkey from reaching the active app.
- **Model Quantization:** Defaults to `int8` on CPU for speed. Check `config.py` for `compute_type`.
- **Injection Gotcha:** Uses clipboard injection because direct keystroke injection (e.g., `pyautogui`) is slow and prone to character encoding issues in different apps.

---

## 🚀 How to Contribute
1. **Environment:** Create a venv and `pip install -r requirements.txt`.
2. **FFmpeg:** Ensure FFmpeg is in your system PATH.
3. **Execution:** Run via `python main.py`.
4. **Debugging:** Logs are saved to `~/.dictation-app/app.log`.

### Future Roadmap
- [ ] Support for multiple languages in a single session.
- [ ] Custom UI themes for the overlay.
- [ ] Direct text injection via accessibility APIs as an alternative to clipboard.
- [ ] Linux/macOS binary distribution via PyInstaller.
