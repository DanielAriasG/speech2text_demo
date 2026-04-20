import io
import os
import urllib.request
from docx import Document
from fpdf import FPDF
from backend.core.export_interface import IExportService

class ExportService(IExportService):
    def __init__(self):
        # Download a Unicode font (Roboto) to support Multilingual chars in PDF
        self.font_path = "Roboto-Regular.ttf"
        if not os.path.exists(self.font_path):
            try:
                # Using a highly stable direct link from the official Google Fonts repository
                url = "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
                urllib.request.urlretrieve(url, self.font_path)
            except Exception as e:
                print(f"Warning: Failed to download Unicode font. {e}")

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
        
        # Apply the Unicode font if it downloaded successfully
        if os.path.exists(self.font_path):
            pdf.add_font("Roboto", "", self.font_path, uni=True)
            pdf.set_font("Roboto", size=12)
        else:
            pdf.set_font("Helvetica", size=12)
            # Fallback to prevent 500 error if font download failed
            transcription = transcription.encode('latin-1', 'replace').decode('latin-1')

        # Use multi_cell to handle long text and line breaks
        pdf.multi_cell(0, 10, text=transcription)

        # In fpdf2, output() can return bytes if no name is given
        return pdf.output()