import io
from docx import Document
from fpdf import FPDF
from typing import List, Dict, Any
from backend.core.export_interface import IExportService

class ExportService(IExportService):
    def _format_segments(self, segments: List[Dict[str, Any]]) -> str:
        if not segments:
            return ""
        output = []
        for s in segments:
            output.append(f"[{s['start']:.2f}s - {s['end']:.2f}s] {s['speaker']}: {s['text']}")
        return "\n".join(output)

    def export_to_txt(self, transcription: str, diarization_segments: List[Dict[str, Any]] = None) -> bytes:
        if diarization_segments:
            return self._format_segments(diarization_segments).encode("utf-8")
        return transcription.encode("utf-8")

    def export_to_docx(self, transcription: str, diarization_segments: List[Dict[str, Any]] = None) -> bytes:
        doc = Document()
        doc.add_heading('Transcription Results', 0)

        if diarization_segments:
            for s in diarization_segments:
                p = doc.add_paragraph()
                p.add_run(f"[{s['start']:.2f}s - {s['end']:.2f}s] ").bold = True
                p.add_run(f"{s['speaker']}: ").italic = True
                p.add_run(s['text'])
        else:
            doc.add_paragraph(transcription)

        output_fp = io.BytesIO()
        doc.save(output_fp)
        return output_fp.getvalue()

    def export_to_pdf(self, transcription: str, diarization_segments: List[Dict[str, Any]] = None) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        if diarization_segments:
            for s in diarization_segments:
                line = f"[{s['start']:.2f}s - {s['end']:.2f}s] {s['speaker']}: {s['text']}"
                pdf.multi_cell(0, 10, text=line)
                pdf.ln(2)
        else:
            pdf.multi_cell(0, 10, text=transcription)

        return pdf.output()
