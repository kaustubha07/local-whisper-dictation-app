import os
import logging
from pathlib import Path
from faster_whisper import WhisperModel
import numpy as np
from config import Config
from typing import Optional

class Transcriber:
    def __init__(self, config: Config):
        self.config = config
        self.model: Optional[WhisperModel] = None
        self.model_dir = Path.home() / ".dictation-app" / "models"
        
        if not self.model_dir.exists():
            self.model_dir.mkdir(parents=True)

    def load_model(self) -> None:
        """Download/load Faster-Whisper model."""
        try:
            logging.info(f"Loading model: {self.config.model_size} on {self.config.device}...")
            # Use Faster-Whisper's implementation
            self.model = WhisperModel(
                self.config.model_size,
                device=self.config.device,
                compute_type=self.config.compute_type,
                download_root=str(self.model_dir)
            )
            logging.info("Model loaded successfully.")
        except Exception as e:
            logging.error(f"Failed to load model: {e}")
            # Auto-fallback to CPU if CUDA fails
            if self.config.device == "cuda":
                logging.warning("Falling back to CPU...")
                self.config.device = "cpu"
                self.config.compute_type = "int8"
                self.load_model()

    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe audio to text."""
        if not self.model:
            logging.warning("Transcriber: Model not loaded.")
            return None
            
        try:
            # Transcribe with faster-whisper
            kwargs = {
                "language": self.config.language,
                "beam_size": 5,
                "vad_filter": False # Already handled in recorder.py
            }
            if self.config.initial_prompt and self.config.initial_prompt.strip():
                kwargs["initial_prompt"] = self.config.initial_prompt.strip()

            segments, info = self.model.transcribe(audio, **kwargs)
            
            # Collect and strip results
            text = " ".join(seg.text.strip() for seg in segments).strip()
            
            # Filter hallucinated filler phrases
            hallucinations = ["", ".", "Thank you.", "Thanks for watching!", "You", "you", "Thank you for watching"]
            if not text or text in hallucinations:
                logging.info("Transcriber: Empty or hallucinated text detected.")
                return None
            
            logging.info(f"Transcription result: '{text}' (prob: {info.language_probability:.2f})")
            return text
            
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return None

    def is_ready(self) -> bool:
        return self.model is not None
