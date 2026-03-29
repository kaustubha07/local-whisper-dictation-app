import time
import pyperclip
import keyboard
import logging
import win32gui
import win32con
from config import Config

class TextInjector:
    def __init__(self, config: Config):
        self.config = config
        self._target_hwnd = None

    def _format_text(self, text: str) -> str:
        """Strip, capitalize and prepend space according to config."""
        text = text.strip()
        if self.config.capitalize_first and text:
            # Capitalize only the first character
            text = text[0].upper() + text[1:]
        
        if self.config.prepend_space:
            text = " " + text
            
        return text

    def save_target_window(self):
        """Snapshots the current foreground window before overlay takes focus."""
        self._target_hwnd = win32gui.GetForegroundWindow()
        logging.debug(f"Saved target HWND: {self._target_hwnd}")

    def inject(self, text: str, overlay_hide_callback=None) -> bool:
        """
        Inject text via clipboard copy-paste.
        If overlay_hide_callback is provided, it's called BEFORE injection
        to let Windows naturally return focus to the underlying application.
        """
        if not text:
            return False
            
        formatted_text = self._format_text(text)
        
        try:
            # Hide the overlay first — this returns focus naturally
            if overlay_hide_callback:
                overlay_hide_callback()
                # 150ms sleep for focus to settle naturally
                time.sleep(0.15)

            # Save current clipboard content
            previous_clipboard = pyperclip.paste()
            
            # Copy new text to clipboard
            pyperclip.copy(formatted_text)
            
            # Short delay for clipboard to settle
            time.sleep(0.05)
            
            # Simulate paste shortcut
            keyboard.send(self.config.paste_key)
            
            # Small delay to ensure paste is finished
            time.sleep(0.1)
            
            # Restore original clipboard
            pyperclip.copy(previous_clipboard)
            
            logging.info(f"Successfully injected: '{formatted_text}'")
            return True
            
        except Exception as e:
            logging.error(f"Failed to inject text: {e}")
            return False
