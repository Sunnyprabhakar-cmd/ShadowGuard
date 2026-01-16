from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import numpy as np
from typing import Any, Dict, List, Optional
import requests
import os

app = FastAPI(title="ML Detection Service", description="Anomaly detection using Isolation Forest")

model_path = os.getenv('MODEL_PATH', '.')

# Load model on startup
try:
    with open(os.path.join(model_path, 'isolation_forest_model.pkl'), 'rb') as f:
        model_data = pickle.load(f)
    iso = model_data['isolation_forest']
    scaler = model_data['scaler']
    threshold = model_data['best_threshold']
except FileNotFoundError:
    iso = None
    scaler = None
    threshold = None

class FeatureData(BaseModel):
    features: List[float]
    context: Optional[Dict[str, Any]] = None

@app.post("/detect")
async def detect_anomaly(data: FeatureData):
    if iso is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    # Scale the features
    features_scaled = scaler.transform([data.features])
    
    # Get anomaly score
    score = iso.decision_function(features_scaled)[0]
    
    # Predict anomaly
    is_anomaly = score < threshold
    
    result = {
        "anomaly_score": float(score),
        "is_anomaly": bool(is_anomaly),
        "threshold": float(threshold)
    }

    context = data.context or {}
    attack_type = str(context.get("attack_type") or context.get("attackType") or "").lower()
    flow_type = str(context.get("flow_type") or "").lower()
    force_classification = (
        flow_type == "anomaly"
        or (attack_type not in {"", "normal_traffic", "benign"} and attack_type != "unknown")
    )

    # Demo traffic should still flow through classification even if the anomaly model
    # is conservative for a specific pattern. Benign flows are still forwarded to the
    # decision engine so they appear on the dashboard as low-severity monitor events.
    try:
        if is_anomaly or force_classification:
            requests.post(
                'http://threat-classification-service:8000/classify',
                json={"features": data.features, "context": context},
                timeout=5
            )
        else:
            requests.post(
                'http://playbook-decision-engine:3000/decide',
                json={
                    "prediction": 0,
                    "probabilities": [1.0],
                    "context": {
                        **context,
                        "attack_type": context.get("attack_type") or "normal_traffic",
                        "flow_type": context.get("flow_type") or "normal"
                    },
                    "sourceIp": context.get("src_ip")
                },
                timeout=5
            )
    except:
        pass

    return result

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": iso is not None}
