import os
from pathlib import Path
import datetime
import logging

class HistoryLogger:
    def __init__(self, path: str = None):
        if path is None:
            self.path = Path.home() / ".dictation-app" / "history.txt"
        else:
            self.path = Path(path)
            
        if not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            
    def log(self, text: str):
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {text}\n")
        except Exception as e:
            logging.error(f"Failed to write history log: {e}")

    def get_recent(self, n: int = 50) -> list[str]:
        if not self.path.exists():
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Return last N lines, most recent first (reversed)
            return [line.strip() for line in lines[-n:]][::-1]
        except Exception as e:
            logging.error(f"Failed to read history log: {e}")
            return []
