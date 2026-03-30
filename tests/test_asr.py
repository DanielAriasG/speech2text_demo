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
        # We need actual audio data since it's not a placeholder anymore
        import io
        import soundfile as sf
        import numpy as np

        sr = 16000
        t = np.linspace(0, 1, sr)
        # 440Hz sine wave doesn't have much speech, but whisper should at least process it.
        # It might return empty string or some hallucination.
        y = 0.5 * np.sin(2 * np.pi * 440 * t)

        buf = io.BytesIO()
        sf.write(buf, y, sr, format='WAV')
        audio_data = buf.getvalue()

        model = ModelRegistry.get_model("whisper")
        res = model.transcribe(audio_data)
        self.assertIsInstance(res, str)

    def test_canary_transcribe(self):
        import io
        import soundfile as sf
        import numpy as np

        sr = 16000
        t = np.linspace(0, 1, sr)
        y = 0.5 * np.sin(2 * np.pi * 440 * t)

        buf = io.BytesIO()
        sf.write(buf, y, sr, format='WAV')
        audio_data = buf.getvalue()

        model = ModelRegistry.get_model("canary")
        res = model.transcribe(audio_data)
        self.assertIsInstance(res, str)

    def test_parakeet_transcribe(self):
        import io
        import soundfile as sf
        import numpy as np

        sr = 16000
        t = np.linspace(0, 1, sr)
        y = 0.5 * np.sin(2 * np.pi * 440 * t)

        buf = io.BytesIO()
        sf.write(buf, y, sr, format='WAV')
        audio_data = buf.getvalue()

        model = ModelRegistry.get_model("parakeet")
        res = model.transcribe(audio_data)
        self.assertIsInstance(res, str)
