from backend.core.export_interface import IExportService

class ExportService(IExportService):
    def export_to_txt(self, transcription: str) -> bytes:
        return transcription.encode("utf-8")

    def export_to_docx(self, transcription: str) -> bytes:
        # Placeholder: returning bytes as if it's a docx
        return b"DOCX Content Placeholder: " + transcription.encode("utf-8")

    def export_to_pdf(self, transcription: str) -> bytes:
        # Placeholder: returning bytes as if it's a pdf
        return b"PDF Content Placeholder: " + transcription.encode("utf-8")
