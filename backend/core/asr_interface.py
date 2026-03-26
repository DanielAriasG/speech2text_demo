from abc import ABC, abstractmethod
from typing import BinaryIO, AsyncGenerator

class IASRModel(ABC):
    @abstractmethod
    def transcribe(self, audio_data: bytes) -> str:
        """Transcribe an audio file from bytes."""
        pass

class IStreamTranscriber(ABC):
    @abstractmethod
    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[str, None]:
        """Transcribe a stream of audio chunks."""
        pass
