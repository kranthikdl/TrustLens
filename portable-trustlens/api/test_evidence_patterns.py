"""
Test script for evidence pattern detection.
Tests all scenarios from the requirements table.
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evidence import analyze_comment, detect_pattern_based_evidence

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_result(test_name, result):
    print(f"\n[TEST] {test_name}")
    print(f"   Status: {result['status']}")
    print(f"   Evidence Present: {result['evidence_present']}")
    print(f"   Verified: {result['verified']}")
    print(f"   TL2 Tooltip: {result['TL2_tooltip']}")
    print(f"   TL3 Detail: {result['TL3_detail']}")
    if result.get('pattern_detection'):
        pd = result['pattern_detection']
        if pd['has_evidence_patterns']:
            print(f"   Pattern Confidence: {pd['confidence']}")
            print(f"   Keywords Found: {len(pd['simple_keyword_matches'])}")
            print(f"   Sentence Patterns: {len(pd['sentence_pattern_matches'])}")
            print(f"   Phrases: {len(pd['phrase_matches'])}")
            print(f"   Credibility Indicators: {len(pd['credibility_matches'])}")

# Test cases covering all scenarios
test_cases = [
    {
        "name": "Verified URL (nytimes.com)",
        "text": "According to this article: https://www.nytimes.com/2024/article",
        "expected_status": "Verified or Unverified (depending on network)"
    },
    {
        "name": "Unverified URL (random blog)",
        "text": "I read this on randomblog.net: https://randomblog.net/post",
        "expected_status": "Unverified or Verified"
    },
    {
        "name": "Citation with 'according to a study'",
        "text": "According to a study published last year, 75% of users prefer this approach.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "Research shows pattern",
        "text": "Research shows that this method is more effective than traditional approaches.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "Data shows pattern",
        "text": "The data shows a clear correlation between these two factors.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "According to + research pattern",
        "text": "According to recent research conducted at MIT, this is the best solution.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "Multiple URLs - mixed verification",
        "text": "Check these sources: https://www.bbc.com/news and also https://fakeblog123.xyz/post",
        "expected_status": "Mixed or Verified/Unverified"
    },
    {
        "name": "No evidence - pure opinion",
        "text": "I think this is the best approach. In my experience, it works well.",
        "expected_status": "None"
    },
    {
        "name": "Citation format detected",
        "text": "This has been proven effective in reducing costs (Smith 2020).",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "Peer-reviewed source mention",
        "text": "This finding was published in a peer-reviewed journal last month.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "Expert attribution",
        "text": "Dr. Johnson, a professor at Stanford, suggests this is the correct approach.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "Statistical claim",
        "text": "Studies found that 68% of participants showed improvement.",
        "expected_status": "Evidence present, unverified"
    },
    {
        "name": "URL + evidence patterns (enhanced credibility)",
        "text": "According to research published at https://nature.com/article, this is proven.",
        "expected_status": "Verified or Unverified (with patterns detected)"
    }
]

def main():
    print_section("Evidence Pattern Detection Test Suite")
    print(f"\nTesting {len(test_cases)} scenarios...")

    results_summary = {
        "Verified": 0,
        "Mixed": 0,
        "Unverified": 0,
        "Evidence present, unverified": 0,
        "None": 0
    }

    for i, test_case in enumerate(test_cases):
        result = analyze_comment(f"test_{i}", test_case["text"])
        print_result(test_case["name"], result)

        status = result["status"]
        if status in results_summary:
            results_summary[status] += 1

    # Summary
    print_section("Test Summary")
    print("\nStatus Distribution:")
    for status, count in results_summary.items():
        if count > 0:
            print(f"  • {status}: {count} comments")

    # Test pattern detection directly
    print_section("Direct Pattern Detection Test")
    test_texts = [
        "According to a study, this works.",
        "Research shows clear benefits.",
        "Data indicates improvement.",
        "No evidence here, just my opinion."
    ]

    for text in test_texts:
        pd = detect_pattern_based_evidence(text)
        print(f"\nText: '{text}'")
        print(f"  Has patterns: {pd['has_evidence_patterns']}")
        print(f"  Confidence: {pd['confidence']}")
        if pd['sentence_pattern_matches']:
            print(f"  Patterns: {[p['pattern'] for p in pd['sentence_pattern_matches']]}")

    print("\n" + "="*70)
    print("[COMPLETE] Testing complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
