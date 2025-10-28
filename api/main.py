# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
import sys
import os
import re
import httpx
import csv  # built-in CSV writer

# Import your toxicity model's predict for the local /predict mirror
from toxicity_model.app import predict as toxicity_predict

# Ensure the filename matches the module below (extract_pure_comments.py)
from extract_pure_comments import extract_comments


app = FastAPI(title="Reddit Ingest API")

# Allow extension pages and localhost to call us.
origins = [
    "http://localhost",
    "http://127.0.0.1:8000",
    "*",  # relax for local dev; tighten in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestPayload(BaseModel):
    filename: str
    data: Dict[str, Any]


class Texts(BaseModel):
    texts: List[str]


def get_next_output_path(directory: str, prefix: str = "toxicity_output", ext: str = ".csv") -> str:
    """
    Returns a path like artifacts/toxicity_output_1.csv, toxicity_output_2.csv, ...
    Scans existing files to pick the next available number.
    """
    os.makedirs(directory, exist_ok=True)
    pat = re.compile(rf"^{re.escape(prefix)}_(\d+){re.escape(ext)}$")
    nums: List[int] = []
    for name in os.listdir(directory):
        m = pat.match(name)
        if m:
            try:
                nums.append(int(m.group(1)))
            except ValueError:
                pass
    nxt = (max(nums) + 1) if nums else 1
    return os.path.join(directory, f"{prefix}_{nxt}{ext}")


def _flatten_rows_for_csv(comments: List[str], predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build flat rows for CSV:
    columns => text, badge_color, prob_<label>, pred_<label> for each label
    Uses 'detailed' if available; otherwise falls back to raw arrays.
    """
    labels: List[str] = predictions.get("labels", [])
    detailed = predictions.get("detailed") or []
    rows: List[Dict[str, Any]] = []

    if detailed:
        # Preferred path: we already have per-item dicts
        for item in detailed:
            row = {"text": item.get("text", ""), "badge_color": item.get("badge_color", "")}
            scores = item.get("scores", {}) or {}
            preds = item.get("predictions", {}) or {}
            # keep label order consistent with predictions["labels"]
            for lab in labels:
                row[f"prob_{lab}"] = scores.get(lab, None)
            for lab in labels:
                row[f"pred_{lab}"] = preds.get(lab, None)
            rows.append(row)
        return rows

    # Fallback: construct from arrays
    probs = predictions.get("probabilities", []) or []
    bin_preds = predictions.get("predictions", []) or []
    badge_colors = predictions.get("badge_colors", []) or []

    n = max(len(comments), len(probs), len(bin_preds), len(badge_colors))
    for i in range(n):
        row = {
            "text": comments[i] if i < len(comments) else "",
            "badge_color": badge_colors[i] if i < len(badge_colors) else "",
        }
        # probabilities
        prob_row = probs[i] if i < len(probs) else []
        for j, lab in enumerate(labels):
            row[f"prob_{lab}"] = prob_row[j] if j < len(prob_row) else None
        # predictions
        pred_row = bin_preds[i] if i < len(bin_preds) else []
        for j, lab in enumerate(labels):
            row[f"pred_{lab}"] = pred_row[j] if j < len(pred_row) else None

        rows.append(row)

    return rows


def _csv_headers(labels: List[str]) -> List[str]:
    # Stable, readable order: text, badge_color, all probs, then all preds
    headers = ["text", "badge_color"]
    headers += [f"prob_{lab}" for lab in labels]
    headers += [f"pred_{lab}" for lab in labels]
    return headers


@app.post("/ingest")
async def ingest(payload: IngestPayload):
    print("==> RECEIVED REDDIT POST PAYLOAD", file=sys.stdout, flush=True)
    print(payload.model_dump_json(indent=2), file=sys.stdout, flush=True)

    # 1) Extract plain comment texts from nested JSON
    comments = extract_comments(payload.model_dump())
    predict_payload = {"texts": comments}

    # 2) Call the toxicity /predict endpoint (same process, different route)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("http://127.0.0.1:8000/predict", json=predict_payload)
            resp.raise_for_status()
            predictions = resp.json()
    except httpx.HTTPError as e:
        msg = f"Failed to call /predict: {e}"
        print(msg, file=sys.stderr, flush=True)
        return {"status": "error", "message": msg}

    # 3) Build flat rows for CSV
    labels = predictions.get("labels", [])
    rows = _flatten_rows_for_csv(comments, predictions)

    # 4) Persist results to CSV file (auto-numbered, safe on Windows)
    out_csv_path = get_next_output_path("artifacts", prefix="toxicity_output", ext=".csv")
    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)

    with open(out_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_csv_headers(labels))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Saved predictions CSV to: {out_csv_path}", file=sys.stdout, flush=True)

    # Return where we saved it, plus quick-access fields for UI convenience
    return {
        "status": "ok",
        "saved_to": out_csv_path,
        "counts": {
            "comments": len(comments),
            "labels": len(labels),
            "rows": len(rows),
        },
        "badge_colors": predictions.get("badge_colors", [])
    }


# Mirror endpoint for direct prediction on arbitrary comments
@app.post("/predict")
def predict_output(comments: Texts):
    return toxicity_predict(comments)


@app.get("/health")
async def health():
    return {"status": "healthy"}
