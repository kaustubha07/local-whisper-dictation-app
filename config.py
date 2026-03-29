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
    hotkey: str = "ctrl+alt+space"  # keyboard format
    paste_key: str = "ctrl+v"         # "cmd+v" on macOS
    sample_rate: int = 16000
    vad_threshold: float = 0.3        # Silero VAD sensitivity 0.0-1.0
    silence_duration_ms: int = 800    # ms of silence to auto-stop recording
    max_recording_seconds: int = 60   # Safety cap on recording length
    prepend_space: bool = True        # Prepend a space before injected text
    capitalize_first: bool = True     # Auto-capitalize first word
    hotkey_mode: str = "toggle"       # "toggle" or "hold"
    initial_prompt: str = ""          # Optional context for Whisper
    gain_boost: float = 1.0           # Extra volume boost multiplier
    vocab_profiles: dict = field(default_factory=lambda: {
        "General": "",
        "Coding": "Python, TypeScript, React, async, function, return, import, class",
        "Medical": "diagnosis, prescription, hypertension, tachycardia, mg, dosage"
    })
    active_profile: str = "General"
    app_profiles: dict = field(default_factory=lambda: {
        "code": "Coding",
        "pycharm64": "Coding",
        "winword": "Medical"
    })
    
    # --- New features config ---
    min_audio_rms: float = 0.01
    confirm_timeout: float = 15.0
    streaming_timeout: float = 30.0
    negate_phrases: set = field(default_factory=lambda: {
        "cancel that", "never mind", "forget it",
        "discard", "nope", "don't inject", "abort"
    })

    def apply_profile(self, name: str) -> bool:
        """Applies a vocabulary profile without saving to disk immediately to prevent spam writes."""
        if name in self.vocab_profiles:
            self.active_profile = name
            self.initial_prompt = self.vocab_profiles[name]
            return True
        return False

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
                    # Filter out keys that aren't valid Config fields to prevent __init__ errors
                    valid_keys = cls.__dataclass_fields__.keys()
                    filtered_data = {k: v for k, v in data.items() if k in valid_keys}
                    config = cls(**filtered_data)
                    logging.info(f"Config: Loaded from {config_file} (Hotkey: {config.hotkey})")
                    return config
            except Exception as e:
                logging.error(f"Config: Failed to load from {config_file}: {e}")
                
        return cls()

    def save(self) -> None:
        config_dir = Path.home() / ".dictation-app"
        config_file = config_dir / "config.json"
        
        # Consistent normalization before saving to disk
        self.hotkey = self.hotkey.replace("<", "").replace(">", "").strip()
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
            
        try:
            with open(config_file, "w") as f:
                json.dump(asdict(self), f, indent=4)
            logging.info(f"Config: Saved successfully to {config_file} (Hotkey: {self.hotkey})")
        except Exception as e:
            logging.error(f"Config: Failed to save to {config_file}: {e}")
