# 🎙️ Technical Summary: Local Whisper Dictation App

## 1. Project Overview
A production-grade, local-first desktop dictation utility built in Python. The application enables system-wide voice-to-text functionality by capturing audio, transcribing it using on-device AI models, and injecting the results into the active cursor position across any application.

### Key Objectives
*   **Privacy & Offline-First:** 100% on-device inference; zero data leaves the system.
*   **Low Latency:** Optimized for near-instant transcription to maintain user flow.
*   **System Agnostic:** Capable of "typing" into any active application via hardware-level hooks and clipboard manipulation.

---

## 2. System Architecture & Components

### A. Orchestration (`main.py`)
The central hub using a multi-threaded architecture to coordinate global event listeners, AI inference, and UI updates without blocking the main event loop (managed by `pystray`).
*   **Threading Model:** 
    - **Main Thread:** System tray event loop (`pystray`).
    - **UI Thread:** Dedicated `tkinter` process for the status overlay.
    - **Listener Thread:** Global low-level hook (`keyboard`) for hotkey detection.
    - **Executor Pool:** Background `ThreadPoolExecutor` for non-blocking ML inference.

### B. Audio & Perception Engine (`engine/recorder.py`)
- **Audio Capture:** Uses `sounddevice` with a high-performance `PortAudio` backend at a 16kHz sample rate (Whisper's native requirement).
- **Voice Activity Detection (VAD):** Integrates **Silero VAD** (via Torch Hub) to post-process raw audio buffers, stripping silence and ensuring only meaningful speech is sent to the transcription engine. Operates with a fine-tuned `vad_threshold=0.3` to catch early quiet syllables.
- **RMS Audio Normalization:** Normalizes raw audio chunks to a consistent target dBFS level before transcription. Features an adjustable user `gain_boost` multiplier to accommodate quieter microphones without manually modifying system sound properties.

### C. Transcription Engine (`engine/transcriber.py`)
- **Model:** Leverages **Faster-Whisper**, a reimplementation of OpenAI's Whisper model using `CTranslate2` for up to 4x faster inference and reduced memory footprint.
- **Context & Accuracy:** Supports passing user-configurable `initial_prompt` text to artificially bias the AI towards niche terminology, heavily improving domain-specific accuracy.
- **Quantization:** Uses `int8` (CPU) or `float16` (CUDA) compute types to optimize performance on standard consumer hardware.
- **Hallucination Filtering:** Implements heuristic filters to catch and discard common "Whisper hallucinations" (e.g., repeating filler phrases or "Thank you for watching" artifacts).

### D. System Injection Engine (`engine/injector.py`)
- **Mechanism:** Implements "Clipboard Injection" (Save -> Copy -> Paste -> Restore).
- **Rationale:** Simulating individual keypresses for long strings is slow and prone to race conditions or unicode encoding errors. Clipboard injection is nearly instantaneous and works across terminal emulators, browsers, and office suites.

### E. Configurable UI (`ui/tray.py`)
- **Advanced Settings:** Users can adjust generic and advanced options intuitively within a Tkinter-powered floating settings window, saving elements directly to a local JSON cache (`config.py`).

---

## 3. Technical Design Decisions & Rationale

| Decision | Rationale |
| :--- | :--- |
| **Python over Electron** | Lower overhead, direct access to the `PortAudio` buffer, and native integration with the PyTorch/Faster-Whisper ecosystem. |
| **Keyboard library over Pynput** | Discovered that `keyboard` provides more reliable "System-wide" global hooks on Windows, bypassing focus issues encountered with `pynput` in certain specialized windows. |
| **Tkinter for Overlay** | Extremely lightweight (~4MB memory footprint) compared to embedding a browser engine for a simple status indicator. |
| **CTranslate2 (Faster-Whisper)** | Essential for "Local AI" to run on standard CPUs without requiring expensive Dedicated GPUs. |

---

## 4. Challenges & Solutions Encountered

### 1. The Global Hotkey "Silencing" Issue
**Problem:** Initial attempts with `pynput` were inconsistent, sometimes failing to trigger when high-priority apps (like full-screen games or administrative terminals) were focused.
**Solution:** Migrated to the `keyboard` library's low-level system hook, which operates closer to the OS driver level on Windows, ensuring 100% trigger reliability.

### 2. UI Conflict & Threading
**Problem:** Both `tkinter` and `pystray` typically demand to be on the "Main Thread."
**Solution:** Architected the `StatusOverlay` with its own `Thread` and `after()` scheduling, allowing it to coexist with the system tray's event loop. Communication between them is managed via a thread-safe `AppState` dataclass.

### 3. Model Hallucinations
**Problem:** Whisper models can generate "empty" or "filler" text when silence or background noise remains in the buffer.
**Solution:** Integrated **Silero VAD** to sanitize the audio BEFORE it reaches the transcriber, significantly reducing false positives and improving the quality of the final output.

---

## 5. Potential Interview Questions

*   **"How do you handle the race condition if a user hits the hotkey while a transcription is already in progress?"**
    > *Answer:* I implemented a thread-safe `AppState` with a `threading.Lock`. If the state is `PROCESSING`, the hotkey press is either ignored or triggers a brief overlay notification, preventing multiple conflicting inference tasks.
*   **"Why use 16kHz audio specifically?"**
    > *Answer:* Whisper was trained on 16kHz audio. Using any other sample rate would require a resampling step (adding latency) or result in significantly lower transcription accuracy.
*   **"What are the limitations of your clipboard injection strategy?"**
    > *Answer:* If a user manually copies something during the ~150ms injection window, their manual copy might be overwritten or restored incorrectly. This was mitigated by keeping the "Paste -> Restore" window as small as possible (using standard `time.sleep` delays).
