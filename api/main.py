# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List
import sys
import os
import re
import json
import httpx

# Import your toxicity model's predict for the local /predict mirror
# Make sure your package/module path is correct.
# Use explicit relative import to ensure we get the correct module
import sys
import os
# Add api directory to path explicitly to avoid importing wrong module
_api_dir = os.path.dirname(os.path.abspath(__file__))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)
from toxicity_model.app import predict as toxicity_predict

# Ensure the filename matches the module below (extract_pure_comments.py)
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from extract_pure_comments import extract_comments
from evidence import analyze_comments as analyze_evidence


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


class EvidencePayload(BaseModel):
    comments: List[Dict[str, str]]  # List of {comment_id: str, text: str}


def get_next_output_path(directory: str, prefix: str = "toxicity_output", ext: str = ".json") -> str:
    """
    Returns a path like artifacts/toxicity_output_1.json, toxicity_output_2.json, ...
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
        # Surface a clear error if the toxicity service isn't reachable
        msg = f"Failed to call /predict: {e}"
        print(msg, file=sys.stderr, flush=True)
        return {"status": "error", "message": msg}

    # 3) Analyze evidence/sources in comments
    # Format comments for evidence analysis (needs comment_id and text)
    comments_for_evidence = [
        {"comment_id": f"comment_{i}", "text": text}
        for i, text in enumerate(comments)
    ]
    evidence_results = analyze_evidence(comments_for_evidence)
    print(f"Analyzed {len(evidence_results)} comments for evidence", file=sys.stdout, flush=True)

    # 4) Persist results to JSON file (auto-numbered, safe on Windows)
    out_path = get_next_output_path("artifacts", prefix="toxicity_output", ext=".json")
    payload_to_save = {
        "source_filename": payload.filename,  # only stored inside JSON
        "comments": comments,
        "toxicity": predictions,
        "evidence": evidence_results
    }

    # Use 'x' to avoid overwriting if called concurrently; fall back to next number if needed
    try:
        with open(out_path, "x", encoding="utf-8") as f:
            json.dump(payload_to_save, f, ensure_ascii=False, indent=2)
    except FileExistsError:
        out_path = get_next_output_path("artifacts", prefix="toxicity_output", ext=".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload_to_save, f, ensure_ascii=False, indent=2)

    print(f"Saved predictions to: {out_path}", file=sys.stdout, flush=True)

    # Return where we saved it, plus quick-access fields for UI convenience
    # Summarize evidence statistics
    evidence_stats = {
        "verified": sum(1 for e in evidence_results if e["status"] == "Verified"),
        "unverified": sum(1 for e in evidence_results if e["status"] == "Unverified"),
        "mixed": sum(1 for e in evidence_results if e["status"] == "Mixed"),
        "none": sum(1 for e in evidence_results if e["status"] == "None")
    }

    return {
        "status": "ok",
        "saved_to": out_path,
        "counts": {
            "comments": len(comments),
            "labels": len(predictions.get("labels", []))
        },
        "badge_colors": predictions.get("badge_colors", []),
        "evidence_stats": evidence_stats
    }


# Mirror endpoint for direct prediction on arbitrary comments
@app.post("/predict")
def predict_output(comments: Texts):
    result = toxicity_predict(comments)
    # Debug: Log what we're returning
    print(f"DEBUG main.py: predict_output result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}", flush=True)
    print(f"DEBUG main.py: badge_colors in result: {'badge_colors' in result if isinstance(result, dict) else 'N/A'}", flush=True)
    return result


@app.get("/health")
async def health():
    return {"status": "healthy"}
