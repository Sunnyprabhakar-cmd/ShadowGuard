from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import numpy as np
from typing import Any, Dict, List, Optional
import requests
import os

app = FastAPI(title="Threat Classification Service", description="Threat classification using Random Forest")

model_path = os.getenv('MODEL_PATH', '.')

# Load model on startup
try:
    with open(os.path.join(model_path, 'random_forest_model.pkl'), 'rb') as f:
        rf = pickle.load(f)
except FileNotFoundError:
    rf = None

class FeatureData(BaseModel):
    features: List[float]
    context: Optional[Dict[str, Any]] = None

@app.post("/classify")
async def classify_threat(data: FeatureData):
    if rf is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Predict
    prediction = rf.predict([data.features])[0]
    probabilities = rf.predict_proba([data.features])[0]
    
    result = {
        "prediction": int(prediction),
        "probabilities": probabilities.tolist(),
        "context": data.context or {},
        "sourceIp": (data.context or {}).get("src_ip")
    }

    # Call decision engine
    try:
        requests.post('http://playbook-decision-engine:3000/decide', json=result, timeout=5)
    except:
        pass

    return result

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": rf is not None}
