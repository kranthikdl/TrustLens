from typing import List, Dict

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from .base import BaseAdapter

# Model config
MODEL_NAME = "unitary/toxic-bert"
LABELS = ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]

# This is ONLY for per-label 0/1 predictions.
# The overall badge is driven by max_prob ranges (0–0.3, 0.3–0.7, 0.7–1.0).
THRESHOLD = 0.5


class ToxicityAdapter(BaseAdapter):
    def __init__(self, cfg: dict | None = None):
        super().__init__(cfg)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None

    def load(self) -> None:
        """Load tokenizer + model once at startup."""
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME
        ).to(self.device)
        self.model.eval()
        self._ready = True

    @staticmethod
    def _badge_color(max_prob: float) -> str:
        """
        Overall toxicity banding:

        0.0 – 0.3   → green  (neutral / low risk)
        0.3 – 0.7   → yellow (mild / borderline)
        0.7 – 1.0   → red    (high toxicity)
        """
        if max_prob >= 0.7:
            return "red"
        if max_prob >= 0.3:
            return "yellow"
        return "green"

    def infer(self, batch: List[Dict]) -> List[Dict]:
        """
        batch: [{"id": str, "text": str}, ...]
        returns: per-item results with probabilities, predictions, and badge_color
        """
        if not self._ready:
            raise RuntimeError("ToxicityAdapter not loaded. Call load() first.")

        if not batch:
            return []

        texts = [item["text"] for item in batch]

        enc = self.tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors="pt",
        ).to(self.device)

        with torch.no_grad():
            logits = self.model(**enc).logits
            probs = torch.sigmoid(logits).cpu().numpy()  # shape: [N, len(LABELS)]

        results: List[Dict] = []

        for item, row in zip(batch, probs):
            row_list = [float(p) for p in row]  # per-label probabilities
            preds = [1 if p >= THRESHOLD else 0 for p in row_list]

            max_prob = max(row_list) if row_list else 0.0
            badge_color = self._badge_color(max_prob)

            results.append(
                {
                    "id": item["id"],
                    "text": item["text"],
                    "labels": LABELS,
                    "probabilities": row_list,
                    "predictions": preds,
                    "badge_color": badge_color,
                    "max_prob": max_prob,  # handy for monitoring/fusion
                }
            )

        return results
