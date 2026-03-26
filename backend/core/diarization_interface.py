from abc import ABC, abstractmethod
from typing import List, Tuple

class IDiarizationService(ABC):
    @abstractmethod
    def diarize(self, audio_data: bytes) -> List[Tuple[float, float, str]]:
        """Perform diarization, returning list of (start, end, speaker_label)."""
        pass
