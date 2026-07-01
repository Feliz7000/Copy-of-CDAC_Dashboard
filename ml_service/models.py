from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class PredictionRequest(BaseModel):
    rows: List[Dict[str, Any]]


class PredictionResponse(BaseModel):
    predictions: List[int]
    probabilities: Optional[List[float]] = None
    ids: Optional[List[str]] = None
