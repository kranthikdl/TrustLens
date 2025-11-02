# heuristics/evidence.py
import re
from dataclasses import dataclass
from typing import List, Dict, Any

# ===== Regex groups =====
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
    re.compile(r"\bvia\s+[A-Z][\w.&-]+", re.I),
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

URL_RX = re.compile(r"https?://[^\s)]+", re.I)
QUOTES_RX = re.compile(r"\"[^\"]+\"|`[^`]+`|^> .*$", re.M)
PUNCT_RUNS_RX = re.compile(r"([!?.,])\1{2,}")

# Keep the profanity list tiny here; you can swap a larger one later.
PROFANITY = [
    "idiot","stupid","moron","trash","loser","shut up"
]
PROF_RX = re.compile(r"\b(" + "|".join(map(re.escape, PROFANITY)) + r")\b", re.I)

def _cap_ratio(text: str) -> float:
    letters = re.sub(r"[^A-Za-z]", "", text or "")
    if not letters: return 0.0
    upp = len(re.sub(r"[^A-Z]", "", text or ""))
    return upp / max(1, len(letters))

@dataclass
class HeuristicsOut:
    features: Dict[str, float]
    tips: List[str]
    evidence_hits: List[str]
    negative_hits: List[str]
    raw: Dict[str, Any]
    score: float  # 0..1

def compute_heuristics(text: str) -> HeuristicsOut:
    text = text or ""

    # counts / measures
    caps_pct = _cap_ratio(text)
    punct_runs = len(PUNCT_RUNS_RX.findall(text))
    quotes = QUOTES_RX.findall(text)
    quote_chars = sum(len(s) for s in quotes)
    quote_pct = quote_chars / max(1, len(text))
    prof_hits = len(PROF_RX.findall(text))

    urls = list(URL_RX.finditer(text))
    links_count = len(urls)

    def _near_url(idx: int, window: int = 80) -> bool:
        return any(abs(idx - m.start()) <= window for m in urls)

    # collect matches
    hits, negs = [], []
    for group in (POS_STRONG, POS_CITATION, POS_COMMON, POS_STATS, POS_LINKY):
        for rx in group:
            for m in rx.finditer(text):
                hits.append(m.group(0))

    for rx in NEG_HEARSAY:
        for m in rx.finditer(text):
            negs.append(m.group(0))

    # score: strong anchors > positives > negatives
    strong_count = sum(1 for rx in POS_STRONG for _ in rx.finditer(text))
    pos_count = len(set(hits)) - strong_count
    neg_count = len(set(negs))

    score = 0.0
    score += min(strong_count, 3) * 0.35
    score += min(pos_count, 5) * 0.10
    score -= min(neg_count, 3) * 0.25

    # proximity boost if any positive within 80 chars of a URL
    proximity_boost = 0.0
    for rx in POS_CITATION + POS_COMMON + POS_STATS:
        m = rx.search(text)
        if m and _near_url(m.start()):
            proximity_boost = 0.15
            break
    score += proximity_boost

    # normalize soft features 0..1 for later fusion debugging (not in score directly)
    features = {
        "capsPct": min(max(caps_pct, 0), 1),
        "punctRuns": min(punct_runs, 5) / 5,
        "quotePct": min(max(quote_pct, 0), 1),
        "profRate": min(prof_hits, 5) / 5,
        "urlCount": min(links_count, 5) / 5,
    }

    # build tips (human-readable)
    tips: List[str] = []
    if strong_count: tips.append(f"Strong citation anchors ({strong_count}).")
    if features["quotePct"] >= 0.15: tips.append("Includes quotes/citations.")
    if links_count >= 1: tips.append(f"{links_count} link(s) present.")
    if prof_hits >= 1: tips.append(f"{prof_hits} profane term(s).")
    if features["capsPct"] >= 0.35: tips.append("High ALL-CAPS ratio.")
    if punct_runs >= 1: tips.append("Repeated punctuation.")

    # clamp score 0..1
    score = max(0.0, min(1.0, score))

    return HeuristicsOut(
        features=features,
        tips=tips[:3],
        evidence_hits=sorted(set(hits))[:5],
        negative_hits=sorted(set(negs))[:3],
        raw={
            "linksCount": links_count,
            "quoteChars": quote_chars,
        },
        score=score,
    )

def fuse_with_model(model_cred: float, heur_score: float, f=None) -> float:
    """
    Blend model credibility (0..1) with heuristics score (0..1).
    Default weights are conservative toward the model.
    """
    w_model = 0.70
    w_heur  = 0.30
    if f and callable(f):
        return f(model_cred, heur_score)
    final = (w_model * model_cred) + (w_heur * heur_score)
    return max(0.0, min(1.0, final))

def badge_from_final(final_score: float) -> str:
    if final_score >= 0.75: return "green"
    if final_score >= 0.45: return "yellow"
    return "red"
