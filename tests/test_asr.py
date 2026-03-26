import unittest
from backend.core.model_registry import ModelRegistry
from backend.models.whisper_impl import WhisperModel
from backend.models.canary_impl import CanaryModel
from backend.models.parakeet_impl import ParakeetModel

class TestASRModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure models are registered for testing
        ModelRegistry.register("whisper", WhisperModel())
        ModelRegistry.register("canary", CanaryModel())
        ModelRegistry.register("parakeet", ParakeetModel())

    def test_whisper_transcribe(self):
        model = ModelRegistry.get_model("whisper")
        res = model.transcribe(b"dummy")
        self.assertEqual(res, "[Whisper Transcription Placeholder]")

    def test_canary_transcribe(self):
        model = ModelRegistry.get_model("canary")
        res = model.transcribe(b"dummy")
        self.assertEqual(res, "[Canary Transcription Placeholder]")

    def test_parakeet_transcribe(self):
        model = ModelRegistry.get_model("parakeet")
        res = model.transcribe(b"dummy")
        self.assertEqual(res, "[Parakeet Transcription Placeholder]")
