"""
Monitored Evidence Analysis Functions
Wraps evidence.py functions with performance monitoring capabilities.
"""
from typing import List, Dict, Any
from evidence import (
    detect_pattern_based_evidence,
    extract_urls_from_text,
    verify_and_classify,
    analyze_comment as original_analyze_comment
)
from performance_monitor import get_monitor


def analyze_comment_monitored(comment_id: str, text: str) -> Dict[str, Any]:
    """
    Analyze a single comment with performance monitoring.
    Tracks latency for pattern detection, URL extraction, and verification.
    """
    monitor = get_monitor()

    # Track pattern detection
    with monitor.measure_operation("pattern_detection"):
        pattern_detection = detect_pattern_based_evidence(text)

    # Track URL extraction
    with monitor.measure_operation("url_extraction"):
        urls = extract_urls_from_text(text)

    # Track URL verification (each URL separately)
    link_results = []
    for url in urls:
        with monitor.measure_operation("url_verification"):
            result = verify_and_classify(url)
            link_results.append(result)

            # Record verification success/failure
            monitor.record_url_verification(result.get("verified", False))

    # Build the complete result (same logic as original analyze_comment)
    if not link_results:
        # No URLs found - check for evidence patterns
        if pattern_detection["has_evidence_patterns"]:
            status = "Evidence present, unverified"
        else:
            status = "None"
    else:
        # URLs found - verify them
        v = sum(1 for r in link_results if r["verified"])
        if v == len(link_results):
            status = "Verified"
        elif v > 0:
            status = "Mixed"
        else:
            status = "Unverified"

    # Build TL2/TL3 tooltips based on status
    if status == "Verified":
        tl2 = "Verified source"
        verified_domains = [r.get('domain', '') for r in link_results if r["verified"]]
        tl3 = f"Verified source: {', '.join(verified_domains)}" if verified_domains else "Verified source"
    elif status == "Mixed":
        tl2 = "Mixed evidence"
        verified_count = sum(r['verified'] for r in link_results)
        unverified_count = sum(not r['verified'] for r in link_results)
        verified_domains = [r.get('domain', '') for r in link_results if r["verified"]]
        unverified_domains = [r.get('domain', '') for r in link_results if not r["verified"]]
        tl3 = f"Mixed evidence: {verified_count} verified ({', '.join(verified_domains)}), {unverified_count} unverified ({', '.join(unverified_domains)})"
    elif status == "Unverified":
        tl2 = "Unverified source ⚠️"
        unverified_domains = [r.get('domain', '') for r in link_results if not r["verified"]]
        tl3 = f"Unverified source: {', '.join(unverified_domains)}" if unverified_domains else "Unverified: links unreachable or error"
    elif status == "Evidence present, unverified":
        tl2 = "Evidence present, unverified"
        pattern_summary = []
        if pattern_detection["sentence_pattern_matches"]:
            pattern_summary.append(f"{len(pattern_detection['sentence_pattern_matches'])} citation patterns")
        if pattern_detection["phrase_matches"]:
            pattern_summary.append(f"{len(pattern_detection['phrase_matches'])} academic phrases")
        if pattern_detection["credibility_matches"]:
            pattern_summary.append(f"{len(pattern_detection['credibility_matches'])} credibility indicators")
        tl3 = f"Evidence cues detected ({', '.join(pattern_summary)}) but no verifiable sources linked"
    else:
        tl2 = "No evidence detected"
        tl3 = "Opinion only; no evidence detected"

    # Record that we processed a comment
    monitor.record_comment_processed()

    return {
        "comment_id": comment_id,
        "text": text,
        "urls": urls,
        "status": status,
        "evidence_present": len(urls) > 0 or pattern_detection["has_evidence_patterns"],
        "verified": status == "Verified",
        "pattern_detection": pattern_detection,
        "results": link_results,
        "TL2_tooltip": tl2,
        "TL3_detail": tl3
    }


def analyze_comments_monitored(comments: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Analyze multiple comments with performance monitoring.
    Tracks overall analysis time and individual operation metrics.
    """
    monitor = get_monitor()
    results = []

    for comment in comments:
        with monitor.measure_operation("full_analysis"):
            result = analyze_comment_monitored(comment["comment_id"], comment["text"])
            results.append(result)

    return results


def get_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics."""
    monitor = get_monitor()
    return monitor.get_all_stats()


def log_performance_stats(filename: str = None) -> str:
    """Log performance statistics to file."""
    monitor = get_monitor()
    return monitor.log_stats(filename)


def print_performance_summary():
    """Print performance summary to console."""
    monitor = get_monitor()
    monitor.print_summary()
