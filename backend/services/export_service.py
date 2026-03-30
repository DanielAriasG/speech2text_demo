import io
from docx import Document
from fpdf import FPDF
from backend.core.export_interface import IExportService

class ExportService(IExportService):
    def export_to_txt(self, transcription: str) -> bytes:
        return transcription.encode("utf-8")

    def export_to_docx(self, transcription: str) -> bytes:
        doc = Document()
        doc.add_heading('Transcription Results', 0)
        doc.add_paragraph(transcription)

        output_fp = io.BytesIO()
        doc.save(output_fp)
        return output_fp.getvalue()

    def export_to_pdf(self, transcription: str) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        # Use multi_cell to handle long text and line breaks
        pdf.multi_cell(0, 10, text=transcription)

        # In fpdf2, output() can return bytes if no name is given
        return pdf.output()
