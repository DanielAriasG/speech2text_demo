from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.services.audio_service import AudioService
from backend.services.transcription_service import TranscriptionService

router = APIRouter()
audio_service = AudioService()
transcription_service = TranscriptionService()

@router.post("/audio/transcriptions")
async def openai_transcribe(
    model: str = Form(...),
    file: UploadFile = File(...)
):
    # This matches the OpenAI API POST /v1/audio/transcriptions
    # Read file
    audio_data = await file.read()

    # Preprocess
    normalized_audio = audio_service.preprocess(audio_data)

    # Transcribe
    try:
        # OpenAI uses "model" instead of "model_name"
        transcription = transcription_service.transcribe_long_form(normalized_audio, model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"text": transcription}
