import logging
import threading
import concurrent.futures
import time
import sys
from pynput import keyboard as pynput_keyboard
import keyboard
from config import Config
from engine.recorder import AudioRecorder
from engine.transcriber import Transcriber
from engine.injector import TextInjector
from engine.history import HistoryLogger
from engine.app_watcher import AppWatcher
from ui.overlay import StatusOverlay
from ui.tray import TrayIcon
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppState:
    status: str = "idle" # idle, recording, processing
    lock: threading.Lock = threading.Lock()

class DictationApp:
    def __init__(self):
        self.config = Config.load()
        self.state = AppState()
        
        # Initialize components
        self.overlay = StatusOverlay()
        self.injector = TextInjector(self.config)
        self.recorder = AudioRecorder(self.config)
        self.transcriber = Transcriber(self.config)
        
        # Use an executor for non-blocking transcription
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        self.history = HistoryLogger()
        self.app_watcher = AppWatcher(self.config, self._on_profile_change)
        
        # Initialize UI tray (will run in main thread)
        self.tray = TrayIcon(self.config, self.toggle_dictation, self.quit)
        
        # Start app watcher
        self.app_watcher.start()
        
        # Model loading (background thread)
        threading.Thread(target=self.transcriber.load_model, daemon=True).start()
        
        # Global hotkey listener (Using 'keyboard' library for better Windows reliability)
        try:
            # Convert pynput format <ctrl>+<alt>+<space> to keyboard format ctrl+alt+space
            kb_hotkey = self.config.hotkey.replace("<", "").replace(">", "")
            keyboard.add_hotkey(kb_hotkey, self.toggle_dictation, suppress=True)
            logging.info(f"Main: Registered global hotkey: {kb_hotkey}")
        except Exception as e:
            logging.error(f"Main: Failed to register hotkey: {e}")

    def _on_profile_change(self, profile_name: str):
        """Callback for when AppWatcher switches vocabulary profiles."""
        if hasattr(self, 'tray') and self.tray:
            self.tray.set_state(self.state.status)

    def toggle_dictation(self):
        """Global hotkey handler."""
        logging.info(f"Main: Hotkey pressed! Current state: {self.state.status}")
        with self.state.lock:
            if self.state.status == "idle":
                self._start_recording()
            elif self.state.status == "recording":
                self._stop_and_transcribe()
            elif self.state.status == "processing":
                logging.info("Main: Still processing current dictation...")
                self.overlay.show_error("Still processing...")

    def _start_recording(self):
        logging.info("Main: Starting recording...")
        self.state.status = "recording"
        self.tray.set_state("recording")
        self.overlay.show_recording()
        self.recorder.start()

    def _stop_and_transcribe(self):
        logging.info("Main: Stopping recording and starting transcription...")
        self.state.status = "processing"
        self.tray.set_state("processing")
        self.overlay.show_processing()
        
        audio = self.recorder.stop()
        if audio is None:
            self.state.status = "idle"
            self.tray.set_state("idle")
            self.overlay.show_error("Nothing detected")
            return

        # Start transcription in executor thread
        self.executor.submit(self._process_audio, audio)

    def _process_audio(self, audio):
        try:
            if not self.transcriber.is_ready():
                self.overlay.show_error("Loading model...")
                # Try to load again if failed before
                self.transcriber.load_model()
                if not self.transcriber.is_ready():
                    self._reset_state_with_error("Model Error")
                    return

            text = self.transcriber.transcribe(audio)
            
            if text:
                self.history.log(text)
                success = self.injector.inject(text)
                if success:
                    self.overlay.show_success(text)
                else:
                    self.overlay.show_error("Injection Failed")
            else:
                self.overlay.show_error("No speech detected")
                
        except Exception as e:
            logging.error(f"Main processing error: {e}")
            self.overlay.show_error("Process Error")
        finally:
            with self.state.lock:
                self.state.status = "idle"
                self.tray.set_state("idle")

    def _reset_state_with_error(self, msg):
        with self.state.lock:
            self.state.status = "idle"
            self.tray.set_state("idle")
            self.overlay.show_error(msg)

    def run(self):
        """Run the application tray icon (blocking)."""
        logging.info("Dictation App is running...")
        try:
            self.tray.run()
        except KeyboardInterrupt:
            self.quit()

    def quit(self, icon=None, item=None):
        """Clean shutdown."""
        logging.info("Shutting down...")
        try:
            keyboard.unhook_all()
        except:
            pass
        self.overlay.hide()
        if self.tray:
            self.tray.stop()
        if hasattr(self, 'app_watcher'):
            self.app_watcher.stop()
        self.executor.shutdown(wait=False)
        sys.exit(0)

if __name__ == "__main__":
    app = DictationApp()
    app.run()
