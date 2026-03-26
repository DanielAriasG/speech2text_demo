from abc import ABC, abstractmethod
from typing import List

class IExportService(ABC):
    @abstractmethod
    def export_to_txt(self, transcription: str) -> bytes:
        """Export transcription to a .txt file."""
        pass

    @abstractmethod
    def export_to_docx(self, transcription: str) -> bytes:
        """Export transcription to a .docx file."""
        pass

    @abstractmethod
    def export_to_pdf(self, transcription: str) -> bytes:
        """Export transcription to a .pdf file."""
        pass
