from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.core.model_registry import ModelRegistry
from backend.services.audio_service import AudioService

router = APIRouter()
audio_service = AudioService()

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

    return {"transcription": transcription}
