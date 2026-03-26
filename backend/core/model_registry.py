from typing import Dict, Type
from backend.core.asr_interface import IASRModel

class ModelRegistry:
    _models: Dict[str, IASRModel] = {}

    @classmethod
    def register(cls, name: str, model: IASRModel):
        cls._models[name] = model

    @classmethod
    def get_model(cls, name: str) -> IASRModel:
        return cls._models.get(name)

    @classmethod
    def list_models(cls):
        return list(cls._models.keys())
