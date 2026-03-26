from abc import ABC, abstractmethod

class IAudioService(ABC):
    @abstractmethod
    def preprocess(self, audio_data: bytes) -> bytes:
        """Normalize audio to a standard format (e.g., 16kHz mono)."""
        pass
