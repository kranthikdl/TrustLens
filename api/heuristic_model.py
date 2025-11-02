# heuristic_model.py
# Standalone "evidence heuristics" scorer for raw text.
# No external deps: only Python stdlib (re, json, argparse, csv, sys).

import re
import json
import argparse
import sys
from dataclasses import dataclass, asdict
from typing import List, Dict, Any


# -----------------------------
# Patterns (edit/extend freely)
# -----------------------------

POS_STRONG = [
    re.compile(r"\bdoi:\s*\d{2}\.\d{4,9}/\S+", re.I),
    re.compile(r"\barXiv:\s*\d{4}\.\d{4,5}(?:v\d+)?\b", re.I),
    re.compile(r"\bpmid:\s*\d{5,9}\b", re.I),
    re.compile(r"\bclinicaltrials\.gov/(?:ct2/show/)?(?:NCT)?\d{8}\b", re.I),
    re.compile(r"\b(preprint|peer[-\s]?reviewed|systematic review|meta[-\s]?analysis)\b", re.I),
    re.compile(r"\b(randomized controlled trial|rct)\b", re.I),
    re.compile(r"\bwhite[-\s]?paper|technical report\b", re.I),
]

POS_CITATION = [
    re.compile(r"\baccording to (the )?(study|report|paper|data|official|guidelines|meta[-\s]?analysis)\b", re.I),
    re.compile(r"\b(as (reported|cited|noted|published) (by|in))\b", re.I),
    re.compile(r"\b(source|sources?)\s*[:\-]\s*", re.I),
    re.compile(r"\b(ref(?:erence)?s?)\s*[:#]\s*", re.I),
    re.compile(r"\bvia\s+[A-Z][\w.&-]+", re.I),        # via WHO / via CDC
    re.compile(r"\bcited (by|in)\b", re.I),
    re.compile(r"\bfact\s*sheet|press\s*release|policy (brief|note)\b", re.I),
    re.compile(r"\bguideline(s)?|recommendation(s)?\b", re.I),
]

POS_COMMON = [
    re.compile(r"\bdata (from|shows?|suggests?|indicates?)\b", re.I),
    re.compile(r"\b(evidence|backed|supported) (by|with)\b", re.I),
    re.compile(r"\b(as per|per)\b", re.I),
    re.compile(r"\bper (the )?(study|paper|report|docs?)\b", re.I),
    re.compile(r"\bthe (numbers|stats|figures) (show|say|suggest)\b", re.I),
    re.compile(r"\b(sources?|citations?) (available|included|below|in comments?)\b", re.I),
    re.compile(r"\b(for reference|for context)\b", re.I),
    re.compile(r"\bmethod(s|ology)?|protocol\b", re.I),
    re.compile(r"\bappendix|supplementary (info|material|materials?)\b", re.I),
    re.compile(r"\b(in|per) (Table|Fig(?:ure)?)\s*[A-Z]?\d+\b", re.I),
    re.compile(r"\b(un|non)[-\s]?biased (source|data)\b", re.I),
]

POS_STATS = [
    re.compile(r"\bp\s*[<=>]\s*0?\.?\d+\b", re.I),
    re.compile(r"\bn\s*=\s*\d{2,}\b", re.I),
    re.compile(r"\b95%\s*ci\b", re.I),
    re.compile(r"\bconfidence interval\b", re.I),
    re.compile(r"\bodds ratio\b", re.I),
    re.compile(r"\bhazard ratio\b", re.I),
    re.compile(r"\br[-\s]?squared|r\^2\b", re.I),
    re.compile(r"\bsample size\b", re.I),
    re.compile(r"\bstatistically (significant|insignificant)\b", re.I),
]

POS_LINKY = [
    re.compile(r"https?://[^\s)]+", re.I),
    re.compile(r"\b\S+\.pdf\b", re.I),
    re.compile(r"\((?:pdf|preprint)\)", re.I),
]

NEG_HEARSAY = [
    re.compile(r"\baccording to (me|my (friend|mom|dad|buddy)|someone|some (guy|dude|rando))\b", re.I),
    re.compile(r"\bsource:\s*(trust me|just trust me|bro)\b", re.I),
    re.compile(r"\b(i (think|guess)|imo|imho|to me)\b", re.I),
    re.compile(r"\bi (heard|read somewhere)\b", re.I),
    re.compile(r"\beveryone (knows|says)\b", re.I),
]

URL_RX       = re.compile(r"https?://[^\s)]+", re.I)
QUOTES_RX    = re.compile(r"\"[^\"]+\"|`[^`]+`|^> .*$", re.M)
PUNCT_RUNS_RX= re.compile(r"([!?.,])\1{2,}")
PROFANITY    = ["idiot","stupid","moron","trash","loser","shut up"]
PROF_RX      = re.compile(r"\b(" + "|".join(map(re.escape, PROFANITY)) + r")\b", re.I)


# -----------------------------
# Scoring helpers
# -----------------------------

def _cap_ratio(text: str) -> float:
    letters = re.sub(r"[^A-Za-z]", "", text or "")
    if not letters:
        return 0.0
    upp = len(re.sub(r"[^A-Z]", "", text or ""))
    return upp / max(1, len(letters))

def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


@dataclass
class HeuristicItem:
    text: str
    heur_score: float            # 0..1 (evidence score only)
    features: Dict[str, float]   # normalized 0..1 feature hints
    tips: List[str]              # short human-readable evidence notes
    evidence_hits: List[str]     # matched positive phrases/anchors
    negative_hits: List[str]     # matched hearsay phrases
    raw: Dict[str, Any]          # extra counters for debugging


# -----------------------------
# Core computation
# -----------------------------

def compute_heuristics_for_text(text: str) -> HeuristicItem:
    text = text or ""

    # Soft signals
    caps_pct    = _cap_ratio(text)
    punct_runs  = len(PUNCT_RUNS_RX.findall(text))
    quotes      = QUOTES_RX.findall(text)
    quote_chars = sum(len(s) for s in quotes)
    quote_pct   = quote_chars / max(1, len(text))
    prof_hits   = len(PROF_RX.findall(text))
    urls        = list(URL_RX.finditer(text))
    links_count = len(urls)

    def near_url(idx: int, window: int = 80) -> bool:
        return any(abs(idx - m.start()) <= window for m in urls)

    # Positive/negative hits
    pos_hits, neg_hits = set(), set()
    for group in (POS_STRONG, POS_CITATION, POS_COMMON, POS_STATS, POS_LINKY):
        for rx in group:
            for m in rx.finditer(text):
                pos_hits.add(m.group(0))
    for rx in NEG_HEARSAY:
        for m in rx.finditer(text):
            neg_hits.add(m.group(0))

    # Score: strong > general positives > negatives; small proximity bonus
    strong_count = sum(1 for rx in POS_STRONG for _ in rx.finditer(text))
    pos_count    = max(0, len(pos_hits) - strong_count)
    neg_count    = len(neg_hits)

    score = 0.0
    score += min(strong_count, 3) * 0.35
    score += min(pos_count,    5) * 0.10
    score -= min(neg_count,    3) * 0.25

    # proximity: any positive phrase close to a URL/DOI/PDF
    proximity_boost = 0.0
    for rx in POS_CITATION + POS_COMMON + POS_STATS:
        m = rx.search(text)
        if m and near_url(m.start()):
            proximity_boost = 0.15
            break
    score = _clamp01(score + proximity_boost)

    # Normalized features (for analysis/UI—NOT added into score here)
    features = {
        "capsPct":   _clamp01(caps_pct),
        "punctRuns": min(punct_runs, 5) / 5.0,
        "quotePct":  _clamp01(quote_pct),
        "profRate":  min(prof_hits, 5) / 5.0,
        "urlCount":  min(links_count, 5) / 5.0,
    }

    # Tips (short)
    tips: List[str] = []
    if strong_count:                    tips.append(f"Strong anchors ({strong_count}).")
    if features["quotePct"] >= 0.15:    tips.append("Includes quotes/citations.")
    if links_count >= 1:                tips.append(f"{links_count} link(s).")
    if prof_hits >= 1:                  tips.append(f"{prof_hits} profane term(s).")
    if features["capsPct"] >= 0.35:     tips.append("High ALL-CAPS.")
    if punct_runs >= 1:                 tips.append("Repeated punctuation.")

    return HeuristicItem(
        text=text,
        heur_score=score,
        features=features,
        tips=tips[:3],
        evidence_hits=sorted(pos_hits)[:5],
        negative_hits=sorted(neg_hits)[:3],
        raw={"linksCount": links_count, "quoteChars": quote_chars},
    )


def heuristic_predict(texts: List[str]) -> Dict[str, Any]:
    """Batch score: returns list of HeuristicItem dicts."""
    out = [asdict(compute_heuristics_for_text(t)) for t in texts]
    return {"count": len(out), "results": out}


# -----------------------------
# CLI
# -----------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Run standalone evidence heuristics on raw text."
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--text", nargs="+", help="One or more text strings")
    g.add_argument("--infile", type=str, help="Path to a UTF-8 file with one text per line")
    p.add_argument("--out", type=str, help="Write JSON output to this path (default: stdout)")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return p.parse_args()

def main():
    args = _parse_args()
    if args.text:
        texts = args.text
    else:
        with open(args.infile, "r", encoding="utf-8") as f:
            texts = [line.rstrip("\n") for line in f if line.strip()]

    res = heuristic_predict(texts)
    js = json.dumps(res, indent=2 if args.pretty else None, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(js)
        print(f"Wrote heuristics JSON to: {args.out}")
    else:
        sys.stdout.write(js + ("\n" if not js.endswith("\n") else ""))

if __name__ == "__main__":
    main()
