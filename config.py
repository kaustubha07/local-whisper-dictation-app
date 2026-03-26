import json
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path

# Ensure config directory exists for logging
config_dir = Path.home() / ".dictation-app"
if not config_dir.exists():
    config_dir.mkdir(parents=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config_dir / "app.log", mode='a')
    ]
)

@dataclass
class Config:
    model_size: str = "base"          # Options: "tiny", "base", "small", "medium"
    language: str = "en"              # None = auto-detect, "en", "hi", "kn", etc.
    device: str = "cpu"               # "cpu" or "cuda"
    compute_type: str = "int8"        # "int8" for CPU, "float16" for CUDA
    hotkey: str = "<ctrl>+<alt>+<space>"  # pynput format
    paste_key: str = "ctrl+v"         # "cmd+v" on macOS
    sample_rate: int = 16000
    vad_threshold: float = 0.5        # Silero VAD sensitivity 0.0-1.0
    silence_duration_ms: int = 800    # ms of silence to auto-stop recording
    max_recording_seconds: int = 60   # Safety cap on recording length
    prepend_space: bool = True        # Prepend a space before injected text
    capitalize_first: bool = True     # Auto-capitalize first word
    hotkey_mode: str = "toggle"       # "toggle" or "hold"

    @classmethod
    def load(cls) -> "Config":
        config_dir = Path.home() / ".dictation-app"
        config_file = config_dir / "config.json"
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
            
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    return cls(**data)
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
                
        return cls()

    def save(self) -> None:
        config_dir = Path.home() / ".dictation-app"
        config_file = config_dir / "config.json"
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
            
        try:
            with open(config_file, "w") as f:
                json.dump(asdict(self), f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
