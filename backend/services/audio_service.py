from backend.core.audio_interface import IAudioService

class AudioService(IAudioService):
    def preprocess(self, audio_data: bytes) -> bytes:
        """
        Normalize audio to 16kHz mono.
        Placeholder logic for now.
        """
        return audio_data
