import io
import librosa
import soundfile as sf
from backend.core.audio_interface import IAudioService

class AudioService(IAudioService):
    def preprocess(self, audio_data: bytes) -> bytes:
        """
        Normalize audio to 16kHz mono.
        """
        # Load audio from bytes
        audio_fp = io.BytesIO(audio_data)
        y, sr = librosa.load(audio_fp, sr=16000, mono=True)

        # Save processed audio to bytes
        output_fp = io.BytesIO()
        sf.write(output_fp, y, 16000, format='WAV')
        return output_fp.getvalue()

    def get_segment(self, audio_data: bytes, start_sec: float, end_sec: float) -> bytes:
        """
        Extract a segment of audio data.
        """
        audio_fp = io.BytesIO(audio_data)
        y, sr = sf.read(audio_fp)

        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        segment_data = y[start_sample:end_sample]

        output_fp = io.BytesIO()
        sf.write(output_fp, segment_data, sr, format='WAV')
        return output_fp.getvalue()
