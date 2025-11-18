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
from evidence import analyze_comments as analyze_evidence, analyze_comment
from evidence_monitored import (
    get_performance_stats,
    log_performance_stats,
    print_performance_summary
)
from output_formatter import format_all_results


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


class SingleComment(BaseModel):
    text: str


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
    # Process each comment individually to handle errors gracefully
    # This ensures one bad URL doesn't break analysis for all comments
    evidence_results = []
    for i, text in enumerate(comments):
        comment_id = f"comment_{i}"
        try:
            result = analyze_comment(comment_id, text)
            evidence_results.append(result)
        except (UnicodeError, ValueError, OSError) as e:
            # Handle DNS/URL resolution errors for individual comments
            # These are expected for malformed URLs
            evidence_results.append({
                "comment_id": comment_id,
                "text": text,
                "urls": [],
                "status": "None",
                "results": [],
                "TL2_tooltip": "Unable to verify sources",
                "TL3_detail": "Could not analyze URLs in this comment"
            })
        except Exception as e:
            # Handle any other unexpected errors for individual comments
            evidence_results.append({
                "comment_id": comment_id,
                "text": text,
                "urls": [],
                "status": "None",
                "results": [],
                "TL2_tooltip": "Analysis error",
                "TL3_detail": "Error analyzing evidence"
            })
    
    print(f"Analyzed {len(evidence_results)} comments for evidence", file=sys.stdout, flush=True)

    # Get performance stats for this batch
    perf_stats = get_performance_stats()

    # 4) Format results according to output structure (include performance stats)
    formatted_output = format_all_results(
        comments=comments,
        toxicity_results=predictions,
        evidence_results=evidence_results,
        source_filename=payload.filename,
        performance_stats=perf_stats
    )

    # 5) Persist results to JSON file (auto-numbered, safe on Windows)
    out_path = get_next_output_path("artifacts", prefix="toxicity_output", ext=".json")
    payload_to_save = formatted_output

    # Use 'x' to avoid overwriting if called concurrently; fall back to next number if needed
    try:
        with open(out_path, "x", encoding="utf-8") as f:
            json.dump(payload_to_save, f, ensure_ascii=False, indent=2)
    except FileExistsError:
        out_path = get_next_output_path("artifacts", prefix="toxicity_output", ext=".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload_to_save, f, ensure_ascii=False, indent=2)

    print(f"Saved predictions to: {out_path}", file=sys.stdout, flush=True)

    # Log performance stats to file
    perf_log_path = log_performance_stats()
    print(f"Performance metrics saved to: {perf_log_path}", file=sys.stdout, flush=True)

    # Print performance summary to console
    print_performance_summary()

    # Return where we saved it, plus quick-access fields for UI convenience
    return {
        "status": "ok",
        "saved_to": out_path,
        "total_comments": formatted_output["total_comments"],
        "summary": formatted_output["summary"],
        "preview": formatted_output["comments"][:3] if len(formatted_output["comments"]) > 0 else [],  # Show first 3 comments as preview
        "performance": perf_stats  # Include real-time performance metrics
    }


# Mirror endpoint for direct prediction on arbitrary comments
@app.post("/predict")
def predict_output(comments: Texts):
    result = toxicity_predict(comments)
    # Debug: Log what we're returning
    print(f"DEBUG main.py: predict_output result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}", flush=True)
    print(f"DEBUG main.py: badge_colors in result: {'badge_colors' in result if isinstance(result, dict) else 'N/A'}", flush=True)
    return result


def determine_badge_color(toxicity_color: str, evidence_status: str) -> str:
    """
    Determine final badge color based on TL1-TL2-TL3 specification.

    Logic per design spec:
    - Red badge: Toxic (any evidence state)
    - Green badge: Neutral + (Verified OR No evidence)
    - Yellow badge: Neutral + Unverified/Mixed OR Mild (any evidence)

    Args:
        toxicity_color: "red" (Toxic), "yellow" (Mild), or "green" (Neutral)
        evidence_status: "Verified", "Unverified", "Mixed", "None", or "Evidence present, unverified"

    Returns:
        Badge color: "red", "green", or "yellow"
    """
    # Map toxicity color to level
    if toxicity_color == "red":
        # Toxic: Always red regardless of evidence
        return "red"

    elif toxicity_color == "yellow":
        # Mild: Always yellow regardless of evidence
        return "yellow"

    else:  # toxicity_color == "green" (Neutral)
        # Neutral: Color depends on evidence
        if evidence_status in ["Verified"]:
            return "green"
        elif evidence_status in ["None"]:
            # No evidence with neutral tone = green
            return "green"
        else:  # "Unverified", "Mixed", or "Evidence present, unverified"
            # Neutral with unverified evidence = yellow
            return "yellow"


@app.post("/analyze-evidence")
def analyze_evidence_single(comment: SingleComment):
    """Analyze evidence for a single comment - for frontend use."""
    import uuid
    try:
        comment_id = f"comment_{uuid.uuid4().hex[:8]}"

        # 1) Analyze evidence
        result = analyze_comment(comment_id, comment.text)

        # 2) Get toxicity level
        toxicity_result = toxicity_predict(Texts(texts=[comment.text]))
        toxicity_color = toxicity_result.get("badge_colors", ["yellow"])[0]
        toxicity_details = toxicity_result.get("detailed", [{}])[0]

        # 3) Determine final badge color based on toxicity + evidence
        badge_color = determine_badge_color(toxicity_color, result["status"])

        # 4) Build response
        return {
            "status": result["status"],
            "badge_color": badge_color,
            "toxicity_color": toxicity_color,  # Include toxicity info for debugging
            "toxicity_scores": toxicity_details.get("scores", {}),
            "evidence": result,
            "TL2_tooltip": result.get("TL2_tooltip", ""),
            "TL3_detail": result.get("TL3_detail", "")
        }
    except (UnicodeError, ValueError, OSError) as e:
        # Handle DNS/URL resolution errors gracefully (e.g., invalid hostnames)
        # These are expected for malformed URLs and should not crash the server
        print(f"Warning: Could not analyze evidence for comment (invalid URL/hostname): {type(e).__name__}", file=sys.stderr, flush=True)

        # Still get toxicity for error case
        try:
            toxicity_result = toxicity_predict(Texts(texts=[comment.text]))
            toxicity_color = toxicity_result.get("badge_colors", ["yellow"])[0]
            badge_color = determine_badge_color(toxicity_color, "None")
        except:
            toxicity_color = "yellow"
            badge_color = "yellow"

        return {
            "status": "None",
            "badge_color": badge_color,
            "toxicity_color": toxicity_color,
            "evidence": {
                "comment_id": "",
                "text": comment.text,
                "urls": [],
                "status": "None",
                "results": [],
                "TL2_tooltip": "Unable to verify sources",
                "TL3_detail": "Could not analyze URLs in this comment"
            },
            "TL2_tooltip": "Unable to verify sources",
            "TL3_detail": "Could not analyze URLs in this comment"
        }
    except Exception as e:
        # Handle any other unexpected errors
        print(f"Error in analyze_evidence_single: {type(e).__name__}: {e}", file=sys.stderr, flush=True)

        # Still get toxicity for error case
        try:
            toxicity_result = toxicity_predict(Texts(texts=[comment.text]))
            toxicity_color = toxicity_result.get("badge_colors", ["yellow"])[0]
            badge_color = determine_badge_color(toxicity_color, "None")
        except:
            toxicity_color = "yellow"
            badge_color = "yellow"

        return {
            "status": "None",
            "badge_color": badge_color,
            "toxicity_color": toxicity_color,
            "evidence": {
                "comment_id": "",
                "text": comment.text,
                "urls": [],
                "status": "None",
                "results": [],
                "TL2_tooltip": "Analysis error",
                "TL3_detail": "Error analyzing evidence"
            },
            "TL2_tooltip": "Analysis error",
            "TL3_detail": "Error analyzing evidence"
        }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/performance")
async def get_performance():
    """Get real-time performance metrics for evidence analysis."""
    stats = get_performance_stats()
    return {
        "status": "ok",
        "metrics": stats
    }


@app.post("/performance/reset")
async def reset_performance():
    """Reset performance monitoring statistics."""
    from performance_monitor import reset_monitor
    reset_monitor()
    return {
        "status": "ok",
        "message": "Performance metrics have been reset"
    }
