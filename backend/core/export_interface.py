from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IExportService(ABC):
    @abstractmethod
    def export_to_txt(self, transcription: str, diarization_segments: List[Dict[str, Any]] = None) -> bytes:
        """Export transcription to a .txt file."""
        pass

    @abstractmethod
    def export_to_docx(self, transcription: str, diarization_segments: List[Dict[str, Any]] = None) -> bytes:
        """Export transcription to a .docx file."""
        pass

    @abstractmethod
    def export_to_pdf(self, transcription: str, diarization_segments: List[Dict[str, Any]] = None) -> bytes:
        """Export transcription to a .pdf file."""
        pass
