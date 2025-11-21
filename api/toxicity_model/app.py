from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import numpy as np
import threading

from .toxicity_adapter import ToxicityAdapter, LABELS


THRESHOLD = 0.5

app = FastAPI(title="Toxicity API", version="1.0")


class Texts(BaseModel):
    texts: List[str]


tox_adapter = ToxicityAdapter()
_adapter_lock = threading.Lock()


def _ensure_adapter_loaded():
    """Ensure the adapter is loaded (thread-safe lazy loading)."""
    if not tox_adapter._ready:
        with _adapter_lock:
            # Double-check after acquiring lock
            if not tox_adapter._ready:
                tox_adapter.load()


@app.on_event("startup")
def startup_event():
    tox_adapter.load()


@app.get("/")
def home():
    return {"message": "Toxicity API is running!"}


def _badge_color_for_row(row_probs: List[float]) -> str:
    # Red   → if any label has score ≥ 0.5
    # Yellow→ if none ≥ 0.7 but max score ∈ [0.3, 0.7)
    # Green → if all scores < 0.3
    arr = np.array(row_probs, dtype=float)
    if (arr >= 0.7).any():
        return "red"
    top = float(arr.max(initial=0.0))
    if top >= 0.3:
        return "yellow"
    return "green"


@app.post("/predict")
def predict(data: Texts) -> Dict[str, Any]:
    # Ensure adapter is loaded before use (lazy loading)
    _ensure_adapter_loaded()
    
    if not data.texts:
        return {
            "labels": LABELS,
            "probabilities": [],
            "predictions": [],
            "badge_colors": [],
            "detailed": [],
        }

    batch = [{"id": str(i), "text": text} for i, text in enumerate(data.texts)]
    adapter_results = tox_adapter.infer(batch)
    # adapter_results is expected to be:
    # [{"id": "0", "text": "...", "probabilities": [...], "predictions": [...]}, ...]

    probabilities: List[List[float]] = []
    predictions: List[List[int]] = []
    badge_colors: List[str] = []
    detailed: List[Dict[str, Any]] = []

    for item in adapter_results:
        probs = item["probabilities"]
        preds = item["predictions"]
        color = _badge_color_for_row(probs)

        probabilities.append(probs)
        predictions.append(preds)
        badge_colors.append(color)

        scores_dict = {label: float(p) for label, p in zip(LABELS, probs)}
        preds_dict = {label: int(v) for label, v in zip(LABELS, preds)}

        detailed.append(
            {
                "id": item.get("id"),
                "text": item.get("text", ""),
                "scores": scores_dict,
                "predictions": preds_dict,
                "badge_color": color,
            }
        )

    return {
        "labels": LABELS,
        "probabilities": probabilities,
        "predictions": predictions,
        "badge_colors": badge_colors,
        "detailed": detailed,
    }
