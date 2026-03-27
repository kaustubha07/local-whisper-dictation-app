# Project Plan / Status Log

## Recently Completed Enhancements
- **RMS Audio Normalization:** Added a robust mathematical audio normalization mechanism to `engine/recorder.py` clamping float signals bounds safely (`[-1.0, 1.0]`) with an adjustable user-configured gain multiplier. 
- **Configurable VAD Parameters:** Lowered the default `vad_threshold` down to `0.3` to catch rapid or quiet speech more accurately without discarding valid recording starts.
- **Contextual Whisper Prompts:** Implemented `initial_prompt` parameter injection block in `engine/transcriber.py`.
- **Advanced GUI Settings (Tkinter):** Expanded the `ui/tray.py` frame geometry and populated an "Advanced Settings" interface segment to expose interactive controls for the AI context vocabulary and microphone gain.