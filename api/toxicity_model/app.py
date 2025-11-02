from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from heuristics.evidence import compute_heuristics, fuse_with_model, badge_from_final

# Load pretrained model
MODEL_NAME = "unitary/toxic-bert"
LABELS = ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]
THRESHOLD = 0.5

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

def _badge_color_for_row(row_probs: np.ndarray) -> str:
    # Rules:
    # Red   → if any label has score ≥ 0.5
    # Yellow→ if none ≥ 0.5 but max score ∈ [0.3, 0.5)
    # Green → if all scores < 0.3
    if (row_probs >= 0.5).any():
        return "red"
    top = float(row_probs.max(initial=0.0))
    if top >= 0.3:
        return "yellow"
    return "green"

@app.post("/predict")
def predict(data: Texts):
    enc = tokenizer(
        data.texts,
        truncation=True,
        padding=True,
        max_length=128,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        logits = model(**enc).logits
        probs = torch.sigmoid(logits).cpu().numpy()  # [N, 6]

    preds = (probs >= THRESHOLD).astype(int).tolist()

    detailed = []
    badge_colors = []
    final_scores = []

    for text, row_probs, row_preds in zip(data.texts, probs, preds):
        # model credibility = inverse of "worst" toxicity
        tox_max = float(np.max(row_probs)) if row_probs.size else 0.0
        model_cred = 1.0 - tox_max  # 1..0 (higher is better)

        heur = compute_heuristics(text)             # HeuristicsOut
        final_score = fuse_with_model(model_cred, heur.score)
        color = badge_from_final(final_score)

        scores_dict = {label: float(p) for label, p in zip(LABELS, row_probs)}
        preds_dict  = {label: int(v)   for label, v in zip(LABELS, row_preds)}

        detailed.append({
            "text": text,
            "scores": scores_dict,
            "predictions": preds_dict,
            "model_cred": model_cred,
            "heuristics": {
                "score": heur.score,
                "features": heur.features,
                "tips": heur.tips,
                "evidence_hits": heur.evidence_hits,
                "negative_hits": heur.negative_hits,
            },
            "final_score": final_score,
            "badge_color": color,
        })
        badge_colors.append(color)
        final_scores.append(final_score)

    return {
        "labels": LABELS,
        "probabilities": probs.tolist(),
        "predictions": preds,
        "badge_colors": badge_colors,
        "final_scores": final_scores,
        "detailed": detailed
    }