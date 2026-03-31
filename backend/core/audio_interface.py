from abc import ABC, abstractmethod

class IAudioService(ABC):
    @abstractmethod
    def preprocess(self, audio_data: bytes) -> bytes:
        """Normalize audio to a standard format (e.g., 16kHz mono)."""
        pass

    @abstractmethod
    def get_segment(self, audio_data: bytes, start_sec: float, end_sec: float) -> bytes:
        """Extract a segment of audio data."""
        pass
