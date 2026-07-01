"""
FastAPI ML Service for Student Analytics Platform
Provides risk prediction, feature importance, and live metrics
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
import logging
from datetime import datetime
import os
import sys
import requests
import pandas as pd
import numpy as np
import io
import joblib
from pathlib import Path

import custom_estimators
import preprocessor

sys.modules.setdefault("ml_service.custom_estimators", custom_estimators)
sys.modules.setdefault("ml_service.preprocessor", preprocessor)

from model_store import FINAL_MODEL_PATH, load_bundle

try:
    from run_all_models import train_from_dataframe
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from run_all_models import train_from_dataframe


app = FastAPI(title="Student Analytics ML Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


class PredictionRequest(BaseModel):
    prn: str
    category_scores: Optional[dict] = None


class PredictionResponse(BaseModel):
    prn: str
    risk_level: str  # 'low', 'medium', 'high'
    risk_score: float
    recommended_actions: List[str]


class FeatureImportance(BaseModel):
    category_code: str
    weight: float
    contribution: float


class PlacementPredictionRequest(BaseModel):
    rows: List[dict]


def _restore_legacy_estimator_attrs(estimator):
    """Patch legacy attributes needed by serialized sklearn objects from older versions."""
    if estimator is None:
        return

    if estimator.__class__.__name__ == "LogisticRegression" and not hasattr(estimator, "multi_class"):
        estimator.multi_class = "auto"

    nested_estimators = getattr(estimator, "estimators_", None)
    if nested_estimators:
        for nested in nested_estimators:
            _restore_legacy_estimator_attrs(nested)

    named_estimators = getattr(estimator, "named_estimators_", None)
    if named_estimators:
        for nested in named_estimators.values():
            _restore_legacy_estimator_attrs(nested)

    steps = getattr(estimator, "steps", None)
    if steps:
        for _, nested in steps:
            _restore_legacy_estimator_attrs(nested)


# ============================================================================
# Prediction Service (Stub Implementation)
# ============================================================================

class PredictionService:
    """ML prediction service using simple threshold rules"""
    
    @staticmethod
    def predict_risk(prn: str, category_scores: dict = None) -> PredictionResponse:
        """
        Predict student risk level based on category scores
        Stub: Uses threshold rules, can be replaced with actual ML model
        """
        if not category_scores:
            # Query database for student scores
            # For now, return stub response
            return PredictionResponse(
                prn=prn,
                risk_level="low",
                risk_score=0.15,
                recommended_actions=[]
            )
        
        # Calculate weighted average
        total_score = sum(category_scores.values())
        max_score = 1500.0
        percentage = (total_score / max_score) * 100
        
        # Risk thresholds
        if percentage >= 75:
            risk_level = "low"
            risk_score = 0.15
            actions = ["Continue current pace"]
        elif percentage >= 60:
            risk_level = "medium"
            risk_score = 0.50
            actions = [
                "Increase study time",
                "Focus on weak categories",
                "Attend counseling sessions"
            ]
        else:
            risk_level = "high"
            risk_score = 0.85
            actions = [
                "Urgent academic intervention",
                "Daily tutoring",
                "Parent notification",
                "Career counseling"
            ]
        
        return PredictionResponse(
            prn=prn,
            risk_level=risk_level,
            risk_score=risk_score,
            recommended_actions=actions
        )


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/ml/predict-risk/{prn}")
async def predict_risk(prn: str):
    """Predict risk level for a student"""
    try:
        service = PredictionService()
        prediction = service.predict_risk(prn)
        return prediction.dict()
    except Exception as e:
        logger.error(f"Prediction error for {prn}: {e}")
        return {"error": str(e)}, 500


@app.post("/ml/predict-bulk/")
async def predict_bulk(requests: List[PredictionRequest]):
    """Predict risk for multiple students"""
    results = []
    service = PredictionService()
    
    for req in requests:
        prediction = service.predict_risk(req.prn, req.category_scores)
        results.append(prediction.dict())
    
    return {"predictions": results, "count": len(results)}


@app.post("/ml/predict-placement/")
async def predict_placement(req: PlacementPredictionRequest):
    """Predict placement status using final_model.joblib"""
    try:
        rows = req.rows
        if not rows:
            return {"predictions": [], "count": 0}
            
        df = pd.DataFrame(rows)
        
        # Load model bundle
        bundle = load_bundle()
        if bundle is None:
            raise HTTPException(status_code=500, detail="final_model.joblib not found")

        model = bundle["model"]
        preprocessor = bundle["preprocessor"]
        selected_raw_columns = bundle["selected_raw_columns"]

        _restore_legacy_estimator_attrs(model)
        
        # Reverse label map for predictions
        code_to_label = {
            0: "Not Placement ready",
            1: "Can Improve",
            2: "Placement ready"
        }
        
        # Ensure all columns exist
        features_dict = {}
        for col in selected_raw_columns:
            if col in df.columns:
                features_dict[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                features_dict[col] = pd.Series(np.nan, index=df.index)
                
        df_features = pd.DataFrame(features_dict, index=df.index)
        
        # Preprocess and Predict
        X_transformed = preprocessor.transform(df_features)
        preds = model.predict(X_transformed)
        
        # Map predictions to string labels
        predicted_labels = [code_to_label.get(p, "Unknown") for p in preds]
        
        return {
            "predictions": predicted_labels,
            "prns": df.get("prn", pd.Series([None]*len(df))).tolist(),
            "count": len(predicted_labels)
        }
        
    except Exception as e:
        logger.error(f"Placement prediction error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/feature-importance/{prn}")
async def feature_importance(prn: str):
    """Get feature importance weights for a student"""
    # Stub: return equal weights for all categories
    categories = {
        'CC': 0.213,
        'MT': 0.320,
        'AP': 0.133,
        'SX': 0.067,
        'ACT': 0.133,
        'PER': 0.133,
    }
    
    return {
        "prn": prn,
        "importance": [
            {
                "category_code": code,
                "weight": weight,
                "contribution": weight * 1500
            }
            for code, weight in categories.items()
        ]
    }


@app.get("/ml/training-status/")
async def training_status():
    """Return accumulated training store stats and last run metadata."""
    from model_store import load_training_meta, load_training_store, load_bundle

    meta = load_training_meta()
    store = load_training_store()
    bundle = load_bundle()
    return {
        "has_model": bundle is not None,
        "total_samples": len(store) if store is not None else 0,
        "last_run": meta.get("last_run"),
        "run_count": len(meta.get("runs", [])),
        "best_xgb_params": meta.get("best_xgb_params"),
    }


@app.post("/ml/train/")
async def train_model_dynamic(
    batch_name: str = Form(...),
    target_csv: UploadFile = File(...),
    fresh: bool = Form(False),
    force_retrain: bool = Form(False),
):
    """
    Incrementally train the placement model.

    Fetches feature rows for the batch, merges with uploaded labels, appends to
    the accumulated training store, and refines the model (XGBoost continues
    from the prior booster when available).
    Pass fresh=true to ignore prior data and retrain from scratch.
    """
    try:
        # 1. Read the uploaded target CSV
        contents = await target_csv.read()
        df_target = pd.read_csv(io.BytesIO(contents))
        
        if 'prn' not in df_target.columns or 'placement_status' not in df_target.columns:
            raise HTTPException(status_code=400, detail="Target CSV must contain 'prn' and 'placement_status' columns.")
        
        df_target['prn'] = df_target['prn'].astype(str).str.strip()
        
        # 2. Fetch feature data from backend API
        base_url = os.getenv("BACKEND_URL", "http://backend:8000")
        username = os.getenv("API_USERNAME", "admin")
        password = os.getenv("API_PASSWORD", "thepassword1234567890")
        
        # Get Token
        session = requests.Session()
        token_resp = session.post(f"{base_url}/api/token/", json={"username": username, "password": password})
        if token_resp.status_code != 200:
            # Fallback to testpassword
            token_resp = session.post(f"{base_url}/api/token/", json={"username": username, "password": "password123"})
            if token_resp.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to authenticate with backend API to fetch features.")
                
        token = token_resp.json().get("access")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Fetch Placement Report JSON
        placement_url = f"{base_url}/api/assessments/reports/placement/?batch_name={batch_name}&format=json"
        report_resp = session.get(placement_url, headers=headers)
        
        if report_resp.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to fetch placement report: {report_resp.text}")
            
        data = report_resp.json()
        rows = data.get("results", data)
        df_features = pd.DataFrame(rows)
        
        if df_features.empty:
            raise HTTPException(status_code=404, detail=f"No data found for batch {batch_name}.")
            
        df_features['prn'] = df_features['prn'].astype(str).str.strip()
        
        # 3. Merge features and targets
        # Drop placement_status if it exists in features to avoid collision
        if 'placement_status' in df_features.columns:
            df_features = df_features.drop(columns=['placement_status'])
            
        df_merged = pd.merge(df_features, df_target[['prn', 'placement_status']], on='prn', how='inner')
        
        if df_merged.empty:
            raise HTTPException(status_code=400, detail="No matching PRNs found between features and target CSV.")
            
        # 4. Train model (incremental by default)
        metrics = train_from_dataframe(
            df_merged,
            incremental=not fresh,
            source_batch=batch_name,
            force_retrain=force_retrain,
        )

        return {
            "status": "success",
            "message": (
                f"Model trained on {metrics.get('merge_stats', {}).get('total', len(df_merged))} "
                f"accumulated records ({metrics.get('mode', 'unknown')} mode)."
            ),
            "metrics": metrics,
        }
        
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint for Live Metrics
# ============================================================================

active_connections: List[WebSocket] = []


@app.websocket("/ws/live-metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for live batch-level metrics"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Send batch-level metrics every 5 seconds
            await asyncio.sleep(5)
            
            # Stub metrics data
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "batches": {
                    "Feb 2026": {
                        "centre_403": {
                            "course_28": {
                                "avg_score": 850.50,
                                "students_at_risk": 12,
                                "top_scorer": 1420.00,
                                "last_updated": datetime.now().isoformat()
                            }
                        }
                    }
                }
            }
            
            await websocket.send_json(metrics)
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
