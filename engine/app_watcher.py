import time
import threading
import logging
import psutil
import platform
from typing import Callable
from config import Config

class AppWatcher:
    def __init__(self, config: Config, on_profile_change: Callable[[str], None]):
        self.config = config
        self.on_profile_change = on_profile_change
        self._stop_event = threading.Event()
        self._thread = None
        self._is_windows = platform.system().lower() == "windows"
        
        if self._is_windows:
            try:
                import ctypes
                self.user32 = ctypes.windll.user32
            except Exception as e:
                logging.warning(f"Failed to load ctypes for AppWatcher: {e}")
                self._is_windows = False

    def get_active_process(self) -> str:
        if not self._is_windows:
            return ""
            
        try:
            hwnd = self.user32.GetForegroundWindow()
            if not hwnd:
                return ""
            
            import ctypes
            from ctypes import wintypes
            pid = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value > 0:
                process = psutil.Process(pid.value)
                name = process.name().lower()
                if name.endswith('.exe'):
                    name = name[:-4]
                return name
        except Exception as e:
            # Silently catch psutil AccessDenied or similar errors
            pass
        return ""

    def _poll(self):
        while not self._stop_event.is_set():
            if self._is_windows:
                process_name = self.get_active_process()
                if process_name in self.config.app_profiles:
                    target_profile = self.config.app_profiles[process_name]
                    if target_profile != self.config.active_profile:
                        success = self.config.apply_profile(target_profile)
                        if success:
                            logging.info(f"AppWatcher: Switched to profile '{target_profile}' for process '{process_name}'")
                            # Trigger callback to update UI
                            if self.on_profile_change:
                                self.on_profile_change(target_profile)
            self._stop_event.wait(2.0)

    def start(self):
        if not self._is_windows:
            logging.info("AppWatcher: Not on Windows, disabled.")
            return
            
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()
        logging.info("AppWatcher: Started polling active processes")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
            logging.info("AppWatcher: Stopped")
