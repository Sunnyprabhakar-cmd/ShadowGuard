from fastapi import FastAPI, BackgroundTasks
import subprocess
import os

app = FastAPI(title="Model Training Service", description="Service for training ML models")

@app.post("/train")
async def train_model(background_tasks: BackgroundTasks):
    """Trigger model training in the background"""
    background_tasks.add_task(run_training)
    return {"message": "Model training started"}

def run_training():
    """Run the training script"""
    try:
        subprocess.run(["python", "train_model.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Training failed: {e}")

@app.get("/health")
async def health():
    return {"status": "healthy"}