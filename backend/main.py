from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.api import transcribe, stream
from backend.core.model_registry import ModelRegistry
from backend.models.whisper_impl import WhisperModel
from backend.models.canary_impl import CanaryModel
from backend.models.parakeet_impl import ParakeetModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load models once upon startup
    ModelRegistry.register("whisper", WhisperModel())
    ModelRegistry.register("canary", CanaryModel())
    ModelRegistry.register("parakeet", ParakeetModel())
    yield
    # Clean up if necessary

app = FastAPI(title="Modular ASR Platform", lifespan=lifespan)

# Include routers
app.include_router(transcribe.router, prefix="/api")
app.include_router(stream.router, prefix="/api/ws")

@app.get("/")
async def root():
    return {"message": "Welcome to the Modular ASR Platform API"}
