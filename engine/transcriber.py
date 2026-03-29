import os
import logging
from pathlib import Path
from faster_whisper import WhisperModel
import numpy as np
from config import Config
from typing import Optional, Generator

class SilentAudioError(Exception):
    """Raised when the audio energy is too low to transcribe."""
    pass

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
        """Transcribe audio to text (sync wrapper for streaming generator)."""
        generator = self.transcribe_stream(audio)
        final_text = ""
        try:
            # Exhaust the generator to get to the return value
            for partial in generator:
                final_text = partial
            return final_text
        except SilentAudioError:
            return None
        except StopIteration as e:
            return e.value
        except Exception as e:
            logging.error(f"Transcriber: Wrap error: {e}")
            return None

    def transcribe_stream(self, audio: np.ndarray) -> Generator[str, None, str]:
        """
        Transcribe audio chunks and yield accumulated text.
        Returns the final string on completion.
        """
        if not self.model:
            logging.warning("Transcriber: Model not loaded.")
            return ""

        # Pre-flight energy check
        rms = np.sqrt(np.mean(audio**2))
        if rms < self.config.min_audio_rms:
            logging.info(f"Transcriber: Silent audio detected (RMS: {rms:.4f} < {self.config.min_audio_rms})")
            raise SilentAudioError("Audio below RMS threshold")

        try:
            kwargs = {
                "language": self.config.language,
                "beam_size": 5,
                "vad_filter": False
            }
            if self.config.initial_prompt and self.config.initial_prompt.strip():
                kwargs["initial_prompt"] = self.config.initial_prompt.strip()

            segments, info = self.model.transcribe(audio, **kwargs)
            
            accumulated = []
            hallucinations = ["", ".", "Thank you.", "Thanks for watching!", "You", "you", "Thank you for watching"]
            
            for seg in segments:
                text = seg.text.strip()
                if text and text not in hallucinations:
                    accumulated.append(text)
                    current_full = " ".join(accumulated).strip()
                    yield current_full

            final_full = " ".join(accumulated).strip()
            
            # Post-loop empty check
            if not final_full:
                logging.info("Transcriber: No segments generated from audio.")
                raise SilentAudioError("No speech detected in segments")

            logging.info(f"Transcription complete: '{final_full}' (prob: {info.language_probability:.2f})")
            return final_full

        except SilentAudioError:
            raise
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            return ""

    def is_ready(self) -> bool:
        return self.model is not None
