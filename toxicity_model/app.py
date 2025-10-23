# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Config
MODEL_NAME = "unitary/toxic-bert"
LABELS = ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]
THRESHOLD = 0.5

# Device + model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).to(device)
model.eval()

app = FastAPI(title="Toxicity API", version="1.0")

class Texts(BaseModel):
    texts: List[str]

@app.get("/")
def home():
    return {"message": "Toxicity API is running!"}

@app.post("/predict")
def predict(data: Texts):
    if not data.texts:
        return {"labels": LABELS, "probabilities": [], "predictions": []}
    enc = tokenizer(
        data.texts,
        truncation=True,
        padding=True,
        max_length=128,
        return_tensors="pt"
    ).to(device)
    with torch.no_grad():
        logits = model(**enc).logits
        probs = torch.sigmoid(logits).cpu().numpy()
    preds = [[1 if p >= THRESHOLD else 0 for p in row] for row in probs]
    return {"labels": LABELS, "probabilities": probs.tolist(), "predictions": preds}

# Run with: uvicorn app:app --host 0.0.0.0 --port 8000 --workers 1
