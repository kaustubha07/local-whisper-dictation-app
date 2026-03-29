import logging
import threading
import concurrent.futures
import time
import sys
from pynput import keyboard as pynput_keyboard
import keyboard
from config import Config
from engine.recorder import AudioRecorder
from engine.transcriber import Transcriber, SilentAudioError
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
        self.decision_event = threading.Event()
        self.confirmed = False
        
        # Use an executor for non-blocking transcription
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        
        self.history = HistoryLogger()
        self.app_watcher = AppWatcher(self.config, self._on_profile_change)
        
        # Initialize UI tray (will run in main thread)
        self.tray = TrayIcon(
            self.config,
            self.toggle_dictation,
            self.quit,
            on_hotkey_change=self._register_hotkey,
            on_restart=self.restart
        )
        
        # Start app watcher
        self.app_watcher.start()
        
        # Model loading (background thread)
        threading.Thread(target=self.transcriber.load_model, daemon=True).start()
        
        # Initial hotkey registration
        self._register_hotkey(self.config.hotkey)

    def _on_profile_change(self, profile_name: str):
        """Callback for when AppWatcher switches vocabulary profiles."""
        if hasattr(self, 'tray') and self.tray:
            self.tray.set_state(self.state.status)

    def toggle_dictation(self):
        """Global hotkey handler."""
        self.injector.save_target_window()
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
        """3-Phase Transcription Pipeline"""
        try:
            # --- PHASE 1: STREAM ---
            final_text = ""
            if not self.transcriber.is_ready():
                self.overlay.show_error("Loading model...")
                self.transcriber.load_model()
                if not self.transcriber.is_ready():
                    self._reset_state_with_error("Model Error")
                    return

            try:
                # Use a generator to get partials
                generator = self.transcriber.transcribe_stream(audio)
                start_time = time.time()
                
                while True:
                    # Enforce timeout on Phase 1
                    if time.time() - start_time > self.config.streaming_timeout:
                        logging.warning("Main: Phase 1 Timeout (30s)")
                        self._reset_state_with_error("Timed Out")
                        return

                    try:
                        partial_text = next(generator)
                        self.overlay.show_streaming(partial_text)
                    except StopIteration as e:
                        final_text = e.value
                        break
            except SilentAudioError:
                logging.info("Main: Silent audio detected in pipeline.")
                self._reset_state_with_error("No speech detected")
                return

            if not final_text:
                self._reset_state_with_error("No speech detected")
                return

            # --- PHASE 2: CONFIRM/CANCEL ---
            self.decision_event.clear()
            self.confirmed = False
            
            def on_confirm():
                self.confirmed = True
                self.decision_event.set()
                
            def on_cancel():
                self.confirmed = False
                self.decision_event.set()

            self.overlay.show_pending_confirm(final_text, on_confirm, on_cancel)
            
            # Block until user decides or timeout
            if not self.decision_event.wait(timeout=self.config.confirm_timeout):
                logging.info("Main: Phase 2 Timeout (Auto-Cancel)")
                self.confirmed = False
            
            # --- PHASE 3: ACT ---
            if self.confirmed:
                # Voice Negation Check
                clean_text = final_text.strip().lower()
                if any(phrase in clean_text for phrase in self.config.negate_phrases):
                    logging.info(f"Main: Negation detected in: '{final_text}'")
                    self.overlay.show_error("Cancelled (Voice)")
                else:
                    self.history.log(final_text)
                    success = self.injector.inject(
                        final_text, 
                        overlay_hide_callback=self.overlay.hide_immediately
                    )
                    if success:
                        self.overlay.show_success(final_text)
                    else:
                        self.overlay.show_error("Injection Failed")
            else:
                logging.info("Main: Confirmation cancelled or timed out.")
                # We show a neutral status for manual cancel
                self._reset_state_with_error("Cancelled")
                
        except Exception as e:
            logging.error(f"Main pipeline error: {e}", exc_info=True)
            self._reset_state_with_error("Error")
        finally:
            self._reset_state()

    def _reset_state(self):
        """Idempotent cleanup of app state."""
        with self.state.lock:
            self.state.status = "idle"
            if hasattr(self, 'tray'):
                self.tray.set_state("idle")
            # Clear events
            self.decision_event.set() 

    def _reset_state_with_error(self, msg):
        with self.state.lock:
            self.state.status = "idle"
            self.tray.set_state("idle")
            self.overlay.show_error(msg)

    def _register_hotkey(self, hotkey_str: str):
        """Unregister old hotkey and register the new one. Safe to call at runtime."""
        try:
            keyboard.unhook_all()  # Clear previous hotkey bindings
            # Normalise: strip pynput-style angle brackets if user typed them
            clean = hotkey_str.replace("<", "").replace(">", "").strip()
            keyboard.add_hotkey(clean, self.toggle_dictation, suppress=True)
            logging.info(f"Main: Registered hotkey: {clean}")
        except Exception as e:
            logging.error(f"Main: Failed to register hotkey '{hotkey_str}': {e}")

    def run(self):
        """Run the application tray icon (blocking)."""
        logging.info("Dictation App is running...")
        try:
            self.tray.run()
        except KeyboardInterrupt:
            self.quit()

    def restart(self, icon=None, item=None):
        """Clean restart — works reliably on Windows."""
        import subprocess
        logging.info("Main: Restarting app...")
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
        
        # Launch new instance and exit current one
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

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
