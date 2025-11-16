from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

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

def normalize_text(text: str) -> str:
    """
    Normalize Unicode characters to ASCII equivalents.
    This prevents misclassification due to special characters like curly quotes.
    """
    # Replace smart/curly quotes with regular quotes
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # single quotes ' '
    text = text.replace('\u201c', '"').replace('\u201d', '"')  # double quotes " "
    # Replace various dashes with regular hyphen
    text = text.replace('\u2013', '-').replace('\u2014', '-')  # en-dash, em-dash
    text = text.replace('\u2026', '...')  # ellipsis
    # Replace other common Unicode punctuation
    text = text.replace('\u00a0', ' ')  # non-breaking space
    return text

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
    print("=== PREDICT FUNCTION CALLED - VERSION WITH BADGE_COLORS ===", flush=True)

    # Normalize texts to handle Unicode characters (e.g., curly quotes)
    normalized_texts = [normalize_text(text) for text in data.texts]

    enc = tokenizer(
        normalized_texts,
        truncation=True,
        padding=True,
        max_length=128,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        logits = model(**enc).logits
        probs = torch.sigmoid(logits).cpu().numpy()  # shape: [N, len(LABELS)]

    # Original binary predictions (kept for backward compatibility)
    preds = (probs >= THRESHOLD).astype(int).tolist()

    # New: badge_color per comment
    badge_colors = [_badge_color_for_row(row) for row in probs]
    
    # Debug: Ensure badge_colors is calculated
    print(f"DEBUG: badge_colors calculated: {badge_colors}", flush=True)

    # New: detailed per-item objects
    detailed = []
    # Use original texts for output, but predictions are based on normalized texts
    for orig_text, row_probs, row_preds, color in zip(data.texts, probs, preds, badge_colors):
        scores_dict = {label: float(p) for label, p in zip(LABELS, row_probs)}
        preds_dict = {label: int(v) for label, v in zip(LABELS, row_preds)}
        detailed.append({
            "text": orig_text,  # Keep original text in output
            "scores": scores_dict,
            "predictions": preds_dict,
            "badge_color": color,
        })

    result = {
        "labels": LABELS,
        "probabilities": probs.tolist(),
        "predictions": preds,
        "badge_colors": badge_colors,     # <— new, array aligned with inputs
        "detailed": detailed              # <— new, rich per-comment view
    }
    
    # Debug: Verify badge_colors is in result
    print(f"DEBUG: result keys: {list(result.keys())}", flush=True)
    print(f"DEBUG: badge_colors in result: {'badge_colors' in result}", flush=True)
    
    return result
