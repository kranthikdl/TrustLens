# reddit_toxicity_pipeline.py
import argparse
import json
import os
import sys
import time
from typing import List, Dict, Any, Optional, Tuple

import requests

# Optional local model mode
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_NAME = "unitary/toxic-bert"
LABELS = ["toxic","severe_toxic","obscene","threat","insult","identity_hate"]
DEFAULT_OUT = "toxicity_model/artifacts/toxicity_outputs.jsonl"
UA = "Mozilla/5.0 (compatible; toxicity-scraper/1.0; +https://example.com)"
REDDIT_TIMEOUT = 20
BATCH_SIZE_DEFAULT = 32


def load_local_model() -> Tuple[AutoTokenizer, AutoModelForSequenceClassification, torch.device]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).to(device)
    model.eval()
    return tokenizer, model, device


def predict_local(texts: List[str], tokenizer, model, device, batch_size: int = BATCH_SIZE_DEFAULT) -> Dict[str, Any]:
    all_probs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        enc = tokenizer(
            batch, truncation=True, padding=True, max_length=128, return_tensors="pt"
        ).to(device)
        with torch.no_grad():
            logits = model(**enc).logits
            probs = torch.sigmoid(logits).cpu().numpy().tolist()
        all_probs.extend(probs)

    preds = [[1 if p >= 0.5 else 0 for p in row] for row in all_probs]
    return {"labels": LABELS, "probabilities": all_probs, "predictions": preds}


def predict_via_api(texts: List[str], api_url: str, batch_size: int = BATCH_SIZE_DEFAULT) -> Dict[str, Any]:
    """POST texts to FastAPI /predict in batches; return concatenated results."""
    labels = None
    all_probs, all_preds = [], []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        resp = requests.post(
            api_url.rstrip("/") + "/predict",
            json={"texts": batch},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        if labels is None:
            labels = data["labels"]
        all_probs.extend(data["probabilities"])
        all_preds.extend(data["predictions"])
    return {"labels": labels or LABELS, "probabilities": all_probs, "predictions": all_preds}


def ensure_dir_for(file_path: str):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def save_jsonl(records: List[Dict[str, Any]], out_path: str):
    ensure_dir_for(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def print_first_n_lines(path: str, n: int = 5):
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= n:
                    break
                sys.stdout.write(line)
        sys.stdout.flush()
    except FileNotFoundError:
        print(f"[warn] File not found: {path}")

def score_to_badge(prob_row, labels):
    max_idx = max(range(len(prob_row)), key=lambda i: prob_row[i])
    top_score = float(prob_row[max_idx])
    top_label = labels[max_idx]

    if any(p >= 0.5 for p in prob_row):
        badge = "red"
    elif top_score >= 0.3:
        badge = "yellow"
    else:
        badge = "green"

    return {"badge_color": badge, "top_label": top_label, "top_score": top_score}



def read_reddit_extraction_json(path: str) -> List[Dict[str, Any]]:
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_items = []
    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        # try common shapes
        for k in ["comments", "items", "data", "records"]:
            if k in data and isinstance(data[k], list):
                raw_items = data[k]
                break
        if not raw_items:
            # Fallback: wrap dict itself if it looks like a comment
            raw_items = [data]

    results = []
    for it in raw_items:
        text = it.get("body") or it.get("text") or it.get("comment") or ""
        if not isinstance(text, str):
            continue
        meta = {k: v for k, v in it.items() if k != "body" and k != "text" and k != "comment"}
        results.append({"text": text.strip(), "meta": meta})
    return results


def _flatten_comment_tree(children: List[Dict[str, Any]], link_id: Optional[str] = None) -> List[Dict[str, Any]]:
    out = []
    for ch in children or []:
        kind = ch.get("kind")
        data = ch.get("data", {})
        if kind == "t1":  # comment
            body = data.get("body")
            if isinstance(body, str) and body.strip():
                out.append({
                    "text": body.strip(),
                    "meta": {
                        "author": data.get("author"),
                        "score": data.get("score"),
                        "created_utc": data.get("created_utc"),
                        "id": data.get("id"),
                        "link_id": data.get("link_id") or link_id,
                        "parent_id": data.get("parent_id"),
                        "permalink": data.get("permalink"),
                    },
                })
            # recurse
            replies = data.get("replies")
            if isinstance(replies, dict):
                out.extend(_flatten_comment_tree(replies.get("data", {}).get("children", []), link_id=data.get("link_id") or link_id))
        # "more" type is ignored here
    return out


def scrape_reddit_thread_comments(thread_url: str, max_comments: int = 1000) -> List[Dict[str, Any]]:
    """
    Fetch comments from a single Reddit thread via its public JSON (no auth).
    """
    if not thread_url.endswith(".json"):
        if thread_url.endswith("/"):
            thread_url = thread_url[:-1]
        thread_url = thread_url + ".json"

    headers = {"User-Agent": UA}
    r = requests.get(thread_url, headers=headers, timeout=REDDIT_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list) or len(data) < 2:
        return []

    # Post metadata in data[0], comments tree in data[1]
    comments_tree = data[1].get("data", {}).get("children", [])
    items = _flatten_comment_tree(comments_tree)
    if max_comments and len(items) > max_comments:
        items = items[:max_comments]
    return items


def scrape_subreddit_hot(subreddit: str, n_posts: int = 5, comments_per_post: int = 200, pause_s: float = 1.0) -> List[Dict[str, Any]]:
    """
    Scrape hot posts and their comments (public JSON).
    """
    headers = {"User-Agent": UA}
    hot_url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={n_posts}"
    resp = requests.get(hot_url, headers=headers, timeout=REDDIT_TIMEOUT)
    resp.raise_for_status()
    posts = resp.json().get("data", {}).get("children", [])
    out = []
    for p in posts:
        post_data = p.get("data", {})
        permalink = post_data.get("permalink")  # e.g., /r/sub/comments/xxxx/title/
        if not permalink:
            continue
        thread_url = "https://www.reddit.com" + permalink
        try:
            items = scrape_reddit_thread_comments(thread_url, max_comments=comments_per_post)
            out.extend(items)
        except Exception as e:
            print(f"[warn] Failed to fetch comments for {thread_url}: {e}")
        time.sleep(pause_s)
    return out


def run_pipeline(
    input_json: Optional[str],
    reddit_url: Optional[str],
    subreddit: Optional[str],
    n_posts: int,
    comments_per_post: int,
    out_path: str,
    use_api: bool,
    api_base: str,
    use_local: bool,
    batch_size: int
):
    # 1) Gather texts
    if input_json:
        items = read_reddit_extraction_json(input_json)
    elif reddit_url:
        items = scrape_reddit_thread_comments(reddit_url, max_comments=comments_per_post)
    elif subreddit:
        items = scrape_subreddit_hot(subreddit, n_posts=n_posts, comments_per_post=comments_per_post)
    else:
        raise SystemExit("Provide one of: --input_json or --reddit_url or --subreddit")

    texts = [it["text"] for it in items if it.get("text")]
    if not texts:
        print("[info] No texts found.")
        save_jsonl([], out_path)
        return

    # 2) Predict
    if use_local:
        tokenizer, model, device = load_local_model()
        result = predict_local(texts, tokenizer, model, device, batch_size=batch_size)
    elif use_api:
        result = predict_via_api(texts, api_base, batch_size=batch_size)
    else:
        # default to API if running without explicit flags
        result = predict_via_api(texts, api_base, batch_size=batch_size)

    labels = result["labels"]
    probs = result["probabilities"]
    preds = result["predictions"]

    # 3) Save JSONL
    
    records = []
    for i, t in enumerate(texts):
        meta = items[i].get("meta", {})
        badge_info = score_to_badge(probs[i], labels)
        records.append({
            "text": t,
            "labels": labels,
            "probabilities": probs[i],
            "predictions": preds[i],
            "badge_color": badge_info["badge_color"],
            "top_label": badge_info["top_label"],
            "top_score": badge_info["top_score"],
            "meta": meta
        })
        save_jsonl(records, out_path)


    # 4) Print first 5 lines for quick validation
    print_first_n_lines(out_path, n=5)


def parse_args():
    ap = argparse.ArgumentParser(description="Reddit → Toxicity → JSONL pipeline")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--input_json", help="Path to Reddit extraction JSON")
    src.add_argument("--reddit_url", help="A single Reddit thread URL (we'll append .json)")
    src.add_argument("--subreddit", help="Scrape hot posts from this subreddit")

    ap.add_argument("--n_posts", type=int, default=5, help="How many hot posts to pull (for --subreddit)")
    ap.add_argument("--comments_per_post", type=int, default=200, help="Max comments per post")
    ap.add_argument("--out", default=DEFAULT_OUT, help="Output JSONL path")
    ap.add_argument("--batch_size", type=int, default=BATCH_SIZE_DEFAULT, help="Batch size for inference")

    run = ap.add_mutually_exclusive_group()
    run.add_argument("--use_api", action="store_true", help="Call FastAPI at --api_base")
    run.add_argument("--use_local", action="store_true", help="Run model locally (no API)")

    ap.add_argument("--api_base", default="http://localhost:8000", help="Base URL for the toxicity API")

    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        input_json=args.input_json,
        reddit_url=args.reddit_url,
        subreddit=args.subreddit,
        n_posts=args.n_posts,
        comments_per_post=args.comments_per_post,
        out_path=args.out,
        use_api=args.use_api,
        api_base=args.api_base,
        use_local=args.use_local,
        batch_size=args.batch_size
    )
