import unittest
from backend.services.audio_service import AudioService
from backend.services.export_service import ExportService
from backend.services.transcription_service import TranscriptionService
from backend.core.model_registry import ModelRegistry
from backend.models.whisper_impl import WhisperModel

class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ModelRegistry.register("whisper", WhisperModel())

    def test_transcription_service_short(self):
        service = TranscriptionService()
        res = service.transcribe_long_form(b"short", "whisper")
        self.assertEqual(res, "[Whisper Transcription Placeholder]")

    def test_transcription_service_long(self):
        # bytes_per_sec is 32000.
        # To trigger chunking, need > 30 * 32000 = 960,000 bytes.
        # Let's give it 1,000,000 bytes.
        # target_secs is 24, so chunk_size is 24 * 32000 = 768,000.
        # chunk 1: 0 to 768,000
        # overlap is 3s * 32000 = 96,000.
        # offset 2: 768,000 - 96,000 = 672,000
        # chunk 2: 672,000 to 1,000,000
        service = TranscriptionService()
        res = service.transcribe_long_form(b"a" * 1000000, "whisper")
        # clean_transcript replaces [ and ] with empty string.
        # Expect "Whisper Transcription Placeholder Whisper Transcription Placeholder"
        expected = "Whisper Transcription Placeholder Whisper Transcription Placeholder"
        self.assertEqual(res, expected)

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
