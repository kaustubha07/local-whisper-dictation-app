import numpy as np
import sounddevice as sd
import torch
import logging
from collections import deque
from config import Config
from typing import Optional

class AudioRecorder:
    def __init__(self, config: Config):
        self.config = config
        self.buffer = deque()
        self.recording = False
        self.stream: Optional[sd.InputStream] = None
        
        # Load Silero VAD
        try:
            self.model, self.utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                                  model='silero_vad',
                                                  force_reload=False,
                                                  trust_repo=True)
            self.get_speech_timestamps, _, self.read_audio, *_ = self.utils
        except Exception as e:
            logging.error(f"Failed to load Silero VAD: {e}")
            self.model = None

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logging.warning(f"Audio status: {status}")
        if self.recording:
            self.buffer.append(indata.copy())

    def start(self) -> None:
        self.buffer.clear()
        self.recording = True
        try:
            self.stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=1,
                dtype='float32',
                callback=self._audio_callback
            )
            self.stream.start()
            logging.info("Recording started.")
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.recording = False

    def stop(self) -> Optional[np.ndarray]:
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if not self.buffer:
            return None
            
        # Concatenate buffered chunks
        audio = np.concatenate(list(self.buffer), axis=0).flatten()
        
        # Post-process with VAD if model is loaded
        if self.model is not None:
            try:
                # Convert to torch tensor
                tensor = torch.from_numpy(audio)
                # Silero expects (batch, samples)
                sampling_rate = self.config.sample_rate
                speech_timestamps = self.get_speech_timestamps(tensor, self.model, sampling_rate=sampling_rate)
                
                if not speech_timestamps:
                    logging.info("VAD: No speech detected.")
                    return None
                    
                # Collect speech parts
                speech_parts = []
                for ts in speech_timestamps:
                    speech_parts.append(audio[ts['start']:ts['end']])
                
                audio = np.concatenate(speech_parts)
                
                # Check minimum speech length (0.3s)
                if len(audio) < 0.3 * sampling_rate:
                    logging.info("VAD: Detected speech too short.")
                    return None
                    
            except Exception as e:
                logging.error(f"VAD error: {e}")
                # Fallback: return original audio if VAD fails
                pass
                
        logging.info(f"Recording stopped. Duration: {len(audio)/self.config.sample_rate:.2f}s")
        return audio
