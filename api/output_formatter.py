"""
Output formatter for TrustLens results.
Combines toxicity and evidence analysis into structured format per the requirements table.
"""
from typing import Dict, Any, List


def get_toxicity_level(badge_color: str) -> str:
    """
    Map badge color to toxicity level.

    Args:
        badge_color: Color from toxicity model (red/yellow/green)

    Returns:
        Toxicity level: Toxic, Mild, or Neutral
    """
    mapping = {
        "red": "Toxic",
        "yellow": "Mild",
        "green": "Neutral"
    }
    return mapping.get(badge_color, "Neutral")


def get_evidence_fields(evidence_status: str) -> Dict[str, Any]:
    """
    Map evidence status to structured evidence fields.

    Args:
        evidence_status: Status from evidence analyzer

    Returns:
        Dict with evidence_present and evidence_verified fields
    """
    status_mapping = {
        "Verified": {"evidence_present": "Yes", "evidence_verified": "Yes"},
        "Mixed": {"evidence_present": "Yes", "evidence_verified": "Partial"},
        "Unverified": {"evidence_present": "Yes", "evidence_verified": "No"},
        "Evidence present, unverified": {"evidence_present": "Yes", "evidence_verified": "No"},
        "None": {"evidence_present": "No", "evidence_verified": "N/A"}
    }
    return status_mapping.get(evidence_status, {"evidence_present": "No", "evidence_verified": "N/A"})


def get_tl1_badge(toxicity_level: str, evidence_present: str = "No", evidence_verified: str = "N/A") -> str:
    """
    Get TL1 badge emoji based on toxicity level and evidence status.

    Badge mapping per TL1 requirements:
    - Toxic (any evidence status) -> Red 🔴
    - Mild (any evidence status) -> Yellow 🟡
    - Neutral + Verified evidence -> Green 🟢
    - Neutral + Unverified evidence -> Yellow 🟡
    - Neutral + No evidence -> Green 🟢

    Args:
        toxicity_level: Toxic, Mild, or Neutral
        evidence_present: Yes or No
        evidence_verified: Yes, No, Partial, or N/A

    Returns:
        Badge emoji
    """
    if toxicity_level == "Toxic":
        return "🔴"  # Red for all toxic content
    elif toxicity_level == "Mild":
        return "🟡"  # Yellow for all mild content
    else:  # Neutral
        # Neutral with unverified evidence gets yellow badge
        if evidence_present == "Yes" and evidence_verified in ["No", "Partial"]:
            return "🟡"  # Yellow for neutral with unverified evidence
        else:
            return "🟢"  # Green for neutral with verified or no evidence


def get_tl2_tooltip(toxicity_level: str, evidence_present: str, evidence_verified: str) -> str:
    """
    Generate TL2 tooltip text based on toxicity and evidence.

    Args:
        toxicity_level: Toxic, Mild, or Neutral
        evidence_present: Yes or No
        evidence_verified: Yes, No, Partial, or N/A

    Returns:
        Tooltip description text
    """
    # Toxic content
    if toxicity_level == "Toxic":
        if evidence_present == "Yes" and evidence_verified == "Yes":
            return "Strong language, verifiable evidence present"
        elif evidence_present == "Yes" and evidence_verified in ["No", "Partial"]:
            return "Strong language, unverifiable evidence"
        else:
            return "Strong language, no evidence"

    # Mild toxicity
    elif toxicity_level == "Mild":
        if evidence_present == "Yes" and evidence_verified == "Yes":
            return "Slightly strong language, verifiable evidence"
        elif evidence_present == "Yes" and evidence_verified in ["No", "Partial"]:
            return "Slightly strong language, unverifiable evidence"
        else:
            return "Slightly strong language, no evidence"

    # Neutral content
    else:  # Neutral
        if evidence_present == "Yes" and evidence_verified == "Yes":
            return "Balanced or neutral tone, verifiable evidence"
        elif evidence_present == "Yes" and evidence_verified in ["No", "Partial"]:
            return "Balanced or neutral tone, unverifiable evidence"
        else:
            return "Balanced or neutral tone, no evidence"


def format_comment_result(
    comment_text: str,
    comment_id: str,
    toxicity_result: Dict[str, Any],
    evidence_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format a single comment's results according to the output structure.

    Args:
        comment_text: The comment text
        comment_id: Comment identifier
        toxicity_result: Result from toxicity model (contains badge_color, scores, predictions)
        evidence_result: Result from evidence analyzer (contains status, urls, etc.)

    Returns:
        Formatted result with TL1, TL2, and all required fields
    """
    # Extract toxicity level
    badge_color = toxicity_result.get("badge_color", "green")
    toxicity_level = get_toxicity_level(badge_color)

    # Extract evidence fields
    evidence_status = evidence_result.get("status", "None")
    evidence_fields = get_evidence_fields(evidence_status)

    # Generate TL1 and TL2
    tl1_badge = get_tl1_badge(
        toxicity_level,
        evidence_fields["evidence_present"],
        evidence_fields["evidence_verified"]
    )
    tl2_tooltip = get_tl2_tooltip(
        toxicity_level,
        evidence_fields["evidence_present"],
        evidence_fields["evidence_verified"]
    )

    # Build structured result
    return {
        "comment_id": comment_id,
        "text": comment_text,

        # TL1 - Badge (Visual Cue)
        "TL1_badge": tl1_badge,

        # TL2 - Tooltip
        "TL2_tooltip": tl2_tooltip,

        # Core analysis fields
        "toxicity_level": toxicity_level,
        "evidence_present": evidence_fields["evidence_present"],
        "evidence_verified": evidence_fields["evidence_verified"],

        # Detailed toxicity data
        "toxicity_scores": toxicity_result.get("scores", {}),
        "toxicity_predictions": toxicity_result.get("predictions", {}),

        # Detailed evidence data
        "evidence_status": evidence_status,
        "evidence_urls": evidence_result.get("urls", []),
        "evidence_results": evidence_result.get("results", []),
        "evidence_TL3_detail": evidence_result.get("TL3_detail", ""),

        # Pattern detection (if available)
        "pattern_detection": evidence_result.get("pattern_detection", {})
    }


def format_all_results(
    comments: List[str],
    toxicity_results: Dict[str, Any],
    evidence_results: List[Dict[str, Any]],
    source_filename: str = "",
    performance_stats: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Format complete analysis results for all comments.

    Args:
        comments: List of comment texts
        toxicity_results: Full toxicity model output
        evidence_results: List of evidence analysis results
        source_filename: Source file name
        performance_stats: Performance monitoring statistics (optional)

    Returns:
        Complete formatted output
    """
    detailed_toxicity = toxicity_results.get("detailed", [])

    formatted_comments = []
    for i, comment_text in enumerate(comments):
        comment_id = f"comment_{i}"

        # Get corresponding toxicity and evidence results
        toxicity_result = detailed_toxicity[i] if i < len(detailed_toxicity) else {}
        evidence_result = evidence_results[i] if i < len(evidence_results) else {}

        formatted_comment = format_comment_result(
            comment_text,
            comment_id,
            toxicity_result,
            evidence_result
        )
        formatted_comments.append(formatted_comment)

    # Summary statistics
    toxicity_summary = {
        "toxic": sum(1 for c in formatted_comments if c["toxicity_level"] == "Toxic"),
        "mild": sum(1 for c in formatted_comments if c["toxicity_level"] == "Mild"),
        "neutral": sum(1 for c in formatted_comments if c["toxicity_level"] == "Neutral")
    }

    evidence_summary = {
        "verified": sum(1 for c in formatted_comments if c["evidence_verified"] == "Yes"),
        "unverified": sum(1 for c in formatted_comments if c["evidence_verified"] == "No"),
        "partial": sum(1 for c in formatted_comments if c["evidence_verified"] == "Partial"),
        "none": sum(1 for c in formatted_comments if c["evidence_present"] == "No")
    }

    output = {
        "source_filename": source_filename,
        "total_comments": len(comments),
        "summary": {
            "toxicity": toxicity_summary,
            "evidence": evidence_summary
        },
        "comments": formatted_comments,

        # Keep raw data for reference
        "raw_data": {
            "toxicity": toxicity_results,
            "evidence": evidence_results
        }
    }

    # Add performance stats if available
    if performance_stats:
        output["performance_metrics"] = performance_stats

    return output
