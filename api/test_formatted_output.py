"""
Test script for the new formatted output structure.
Generates a sample output file using the output_formatter module.
"""
import sys
import os
import io
import json

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evidence import analyze_comments as analyze_evidence
from output_formatter import format_all_results

# Sample test data
test_comments = [
    "This is complete garbage and anyone who believes this is an idiot!",
    "According to research published at https://www.nature.com/articles/article1, this approach shows promise.",
    "I think this might work, but I'm not entirely sure. Just my opinion.",
    "Check out this article: https://www.bbc.com/news/article123",
    "Data from a recent study shows 75% improvement in outcomes.",
]

def create_mock_toxicity_results(comments):
    """Create mock toxicity results for testing."""
    # Simulate different toxicity levels
    detailed = [
        {
            "text": comments[0],
            "scores": {"toxic": 0.85, "severe_toxic": 0.12, "obscene": 0.65, "threat": 0.05, "insult": 0.78, "identity_hate": 0.03},
            "predictions": {"toxic": 1, "severe_toxic": 0, "obscene": 1, "threat": 0, "insult": 1, "identity_hate": 0},
            "badge_color": "red"
        },
        {
            "text": comments[1],
            "scores": {"toxic": 0.02, "severe_toxic": 0.01, "obscene": 0.01, "threat": 0.01, "insult": 0.01, "identity_hate": 0.01},
            "predictions": {"toxic": 0, "severe_toxic": 0, "obscene": 0, "threat": 0, "insult": 0, "identity_hate": 0},
            "badge_color": "green"
        },
        {
            "text": comments[2],
            "scores": {"toxic": 0.35, "severe_toxic": 0.05, "obscene": 0.08, "threat": 0.02, "insult": 0.12, "identity_hate": 0.01},
            "predictions": {"toxic": 0, "severe_toxic": 0, "obscene": 0, "threat": 0, "insult": 0, "identity_hate": 0},
            "badge_color": "yellow"
        },
        {
            "text": comments[3],
            "scores": {"toxic": 0.03, "severe_toxic": 0.01, "obscene": 0.02, "threat": 0.01, "insult": 0.01, "identity_hate": 0.01},
            "predictions": {"toxic": 0, "severe_toxic": 0, "obscene": 0, "threat": 0, "insult": 0, "identity_hate": 0},
            "badge_color": "green"
        },
        {
            "text": comments[4],
            "scores": {"toxic": 0.15, "severe_toxic": 0.02, "obscene": 0.03, "threat": 0.01, "insult": 0.05, "identity_hate": 0.01},
            "predictions": {"toxic": 0, "severe_toxic": 0, "obscene": 0, "threat": 0, "insult": 0, "identity_hate": 0},
            "badge_color": "green"
        }
    ]

    return {
        "labels": ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"],
        "probabilities": [[d["scores"][label] for label in ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]] for d in detailed],
        "predictions": [[d["predictions"][label] for label in ["toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"]] for d in detailed],
        "badge_colors": [d["badge_color"] for d in detailed],
        "detailed": detailed
    }

def main():
    print("="*70)
    print("  Testing New Formatted Output Structure")
    print("="*70)

    # Analyze evidence
    print("\n[1] Analyzing evidence...")
    comments_for_evidence = [
        {"comment_id": f"comment_{i}", "text": text}
        for i, text in enumerate(test_comments)
    ]
    evidence_results = analyze_evidence(comments_for_evidence)
    print(f"    ✓ Analyzed {len(evidence_results)} comments")

    # Create mock toxicity results
    print("\n[2] Creating toxicity analysis...")
    toxicity_results = create_mock_toxicity_results(test_comments)
    print(f"    ✓ Generated toxicity results for {len(test_comments)} comments")

    # Format results
    print("\n[3] Formatting output...")
    formatted_output = format_all_results(
        comments=test_comments,
        toxicity_results=toxicity_results,
        evidence_results=evidence_results,
        source_filename="test_formatted_output.json"
    )
    print("    ✓ Output formatted")

    # Save to file
    output_path = os.path.join("artifacts", "formatted_output_sample.json")
    os.makedirs("artifacts", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_output, f, ensure_ascii=False, indent=2)
    print(f"\n[4] Saved to: {output_path}")

    # Display summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"\nTotal Comments: {formatted_output['total_comments']}")
    print(f"\nToxicity Distribution:")
    for level, count in formatted_output['summary']['toxicity'].items():
        print(f"  • {level.capitalize()}: {count}")

    print(f"\nEvidence Distribution:")
    for status, count in formatted_output['summary']['evidence'].items():
        print(f"  • {status.capitalize()}: {count}")

    # Display sample comment results
    print("\n" + "="*70)
    print("  SAMPLE COMMENT RESULTS")
    print("="*70)

    for i, comment in enumerate(formatted_output['comments'][:3]):
        print(f"\n[Comment {i+1}]")
        print(f"Text: {comment['text'][:60]}...")
        print(f"TL1 Badge: {comment['TL1_badge']}")
        print(f"TL2 Tooltip: {comment['TL2_tooltip']}")
        print(f"Toxicity Level: {comment['toxicity_level']}")
        print(f"Evidence Present: {comment['evidence_present']}")
        print(f"Evidence Verified: {comment['evidence_verified']}")

    print("\n" + "="*70)
    print("[COMPLETE] Test finished successfully!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
