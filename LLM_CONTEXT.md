# Dictation App: Context for AI/LLM Assistants

> **Note to AI Systems:** Read this document first to understand the application architecture, boundaries, and technical constraints before making changes to the codebase.

## 1. Project Overview
This is a local-first, privacy-focused desktop dictation application written in Python. It captures microphone audio, filters out silence using VAD (Voice Activity Detection), transcribes speech locally using the `faster-whisper` AI model, and seamlessly injects the transcribed text into the user's active application via clipboard manipulation.

## 2. Technical Stack
*   **Language:** Python 3.9+ 
*   **Audio Capture:** `sounddevice` (PortAudio backend, **float32** format, 16kHz).
*   **VAD:** Silero VAD (PyTorch).
*   **Transcription:** `faster-whisper` (CTranslate2).
*   **System Hooks:** `keyboard` library (for global Windows hotkeys).
*   **Desktop UI:** `pystray` (System Tray) + `tkinter` (Settings window + Status Overlays).

## 3. Core Architecture & File Structure

### `main.py`
The orchestrator. It manages the multi-threaded operation of the app.
*   Runs `pystray` in the main thread (blocking).
*   Registers global keyboard hooks (e.g. `ctrl+alt+space`) using the `keyboard` module.
*   **Dynamic Hotkeys**: Uses `_register_hotkey` to allow re-hooking at runtime without restarts.
*   **Robust Restart**: Implements a `restart()` method using `subprocess.Popen` for clean process replacement on Windows.
*   Spawns a `ThreadPoolExecutor` for background `faster-whisper` inference to prevent UI/hotkey blocking.

### `config.py`
Defines the `Config` `dataclass` and handles JSON persistence to `~/.dictation-app/config.json`.
*   Stores settings like `vad_threshold` (0.3), `gain_boost` (1.0), `initial_prompt`, and `model_size`.
*   **Normalization**: Automatically cleans hotkey strings (e.g., stripping `<>` brackets) during `save()` to ensure library compatibility.

### `engine/recorder.py`
Audio perception engine (`AudioRecorder` class).
*   Records live audio buffers.
*   Sanitizes audio using Silero VAD to drop dead silence or short noises.
*   Applies **RMS Audio Normalization**: Dynamically adjusts float32 audio volume according to `config.gain_boost` and clamps bounds strictly to `[-1.0, 1.0]` before Whisper processes it.

### `engine/transcriber.py`
Transcription handler (`Transcriber` class).
*   Loads `faster-whisper` securely.
*   Intercepts `config.initial_prompt` keyword arguments to dynamically adjust transcription grammar context.
*   Uses `int8` on CPU.

### `engine/injector.py`
System typist (`TextInjector` class).
*   Employs **Clipboard Injection**: Because simulating keypresses is buggy and slow for long sentences, this system temporarily backs up the user's text clipboard, pastes the newly transcribed text directly to the OS cursor position, and seamlessly restores their old clipboard data.

### `ui/tray.py`
Settings & Overlay GUI (`TrayIcon` class).
*   Uses `pystray` for the taskbar icon.
*   **Thread-Safe Settings**: Spawns `tkinter` elements in isolated background threads.
*   **Direct Widget Access**: To avoid synchronization issues between threads, the UI avoids `tk.StringVar` for input fields, instead using direct widget `.get()` calls (e.g., `hotkey_entry.get()`) during save operations.

## 4. Key Constraints for Future AI Modifications
1.  **Audio Formats:** `faster-whisper` and Silero VAD efficiently handle native `float32` variables; do NOT cast audio internally to `int16` unless modifying external file-save logic.
2.  **Global Hotkeys:** The app uses the `keyboard` module over `pynput` as it provides lower-level hooks natively on Windows that are unaffected by Admin-level focused windows. Ensure hotkeys are passed in `ctrl+alt+space` format (no brackets).
3.  **UI Thread Syncing:** Tkinter `StringVar` can be unreliable across threads. Always use direct widget access or `root.update_idletasks()` when reading settings from an asynchronous window.
4.  **App State Syncing:** Thread-locks (`threading.Lock`) manage the UI status strings to prevent race conditions during rapid audio detection.

## 5. Testing & Running
*   To start the app: `python main.py`
*   Dependency tracking: Kept strictly barebones within `requirements.txt`. Do not introduce large UI frameworks (like PyQt/PySide) without user authorization, to maintain a tiny resource profile.
