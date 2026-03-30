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
        import io
        import soundfile as sf
        import numpy as np

        sr = 16000
        t = np.linspace(0, 1, sr)
        y = 0.5 * np.sin(2 * np.pi * 440 * t)

        buf = io.BytesIO()
        sf.write(buf, y, sr, format='WAV')
        audio_data = buf.getvalue()

        service = TranscriptionService()
        res = service.transcribe_long_form(audio_data, "whisper")
        self.assertIsInstance(res, str)

    def test_transcription_service_long(self):
        import io
        import soundfile as sf
        import numpy as np

        # Create 40s of audio to trigger chunking (> 30s)
        sr = 16000
        t = np.linspace(0, 40, sr * 40)
        y = 0.5 * np.sin(2 * np.pi * 440 * t)

        buf = io.BytesIO()
        sf.write(buf, y, sr, format='WAV')
        audio_data = buf.getvalue()

        service = TranscriptionService()
        res = service.transcribe_long_form(audio_data, "whisper")
        self.assertIsInstance(res, str)

    def test_audio_preprocess(self):
        import io
        import soundfile as sf
        import numpy as np
        service = AudioService()

        # Create a simple 1s sine wave at 44.1kHz
        sr = 44100
        t = np.linspace(0, 1, sr)
        y = 0.5 * np.sin(2 * np.pi * 440 * t)

        input_wav = io.BytesIO()
        sf.write(input_wav, y, sr, format='WAV')
        data = input_wav.getvalue()

        processed_data = service.preprocess(data)
        self.assertNotEqual(processed_data, data)

        # Verify processed data is 16kHz
        output_wav = io.BytesIO(processed_data)
        y_out, sr_out = sf.read(output_wav)
        self.assertEqual(sr_out, 16000)

    def test_export_txt(self):
        service = ExportService()
        transcription = "Hello"
        res = service.export_to_txt(transcription)
        self.assertEqual(res, b"Hello")

    def test_export_pdf(self):
        service = ExportService()
        transcription = "Hello World"
        res = service.export_to_pdf(transcription)
        # Check for PDF header
        self.assertTrue(res.startswith(b"%PDF"))
