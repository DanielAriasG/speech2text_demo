from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.core.model_registry import ModelRegistry
from backend.services.audio_service import AudioService
from backend.diarization.speaker_id import PyannoteDiarization

router = APIRouter()
audio_service = AudioService()
diarization_service = PyannoteDiarization()

@router.post("/transcribe")
async def transcribe_audio(
    model_name: str = Form("whisper"),
    file: UploadFile = File(...)
):
    # 1. Read file
    audio_data = await file.read()

    # 2. Preprocess audio
    normalized_audio = audio_service.preprocess(audio_data)

    # 3. Get model from registry (DIP: depends on abstraction)
    model = ModelRegistry.get_model(model_name)
    if not model:
        raise HTTPException(status_code=400, detail=f"Model {model_name} not found")

    transcription = model.transcribe(normalized_audio)

    # 4. Diarization
    diarization_result = diarization_service.diarize(normalized_audio)

    # Construct structured response with segments
    segments = []
    if len(diarization_result) > 0:
        words = transcription.split()
        words_per_segment = max(1, len(words) // len(diarization_result))

        for i, (start, end, speaker) in enumerate(diarization_result):
            segment_text = " ".join(words[i * words_per_segment : (i + 1) * words_per_segment])
            if i == len(diarization_result) - 1:
                segment_text = " ".join(words[i * words_per_segment :])

            segments.append({
                "start": start,
                "end": end,
                "speaker": speaker,
                "text": segment_text
            })
    else:
        segments.append({
            "start": 0.0,
            "end": 0.0,
            "speaker": "Unknown",
            "text": transcription
        })

    return {
        "transcription": transcription,
        "segments": segments
    }
