import time
import pyperclip
import keyboard
import logging
from config import Config

class TextInjector:
    def __init__(self, config: Config):
        self.config = config

    def _format_text(self, text: str) -> str:
        """Strip, capitalize and prepend space according to config."""
        text = text.strip()
        if self.config.capitalize_first and text:
            # Capitalize only the first character
            text = text[0].upper() + text[1:]
        
        if self.config.prepend_space:
            text = " " + text
            
        return text

    def inject(self, text: str) -> bool:
        """Inject text via clipboard copy-paste."""
        if not text:
            return False
            
        formatted_text = self._format_text(text)
        
        try:
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
