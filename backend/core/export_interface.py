from abc import ABC, abstractmethod
from typing import List, Union

class IExportService(ABC):
    @abstractmethod
    def export_to_txt(self, data: Union[str, list]) -> bytes:
        """Export transcription to a .txt file."""
        pass

    @abstractmethod
    def export_to_docx(self, data: Union[str, list]) -> bytes:
        """Export transcription to a .docx file."""
        pass

    @abstractmethod
    def export_to_pdf(self, data: Union[str, list]) -> bytes:
        """Export transcription to a .pdf file."""
        pass