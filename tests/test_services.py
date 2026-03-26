import unittest
from backend.services.audio_service import AudioService
from backend.services.export_service import ExportService

class TestServices(unittest.TestCase):
    def test_audio_preprocess(self):
        service = AudioService()
        data = b"some data"
        self.assertEqual(service.preprocess(data), data)

    def test_export_txt(self):
        service = ExportService()
        transcription = "Hello"
        res = service.export_to_txt(transcription)
        self.assertEqual(res, b"Hello")

    def test_export_pdf(self):
        service = ExportService()
        transcription = "Hello"
        res = service.export_to_pdf(transcription)
        self.assertIn(b"PDF Content Placeholder", res)
