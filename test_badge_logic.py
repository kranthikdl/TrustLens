"""
Test script to verify TrustLens badge logic with comprehensive scenarios
Tests all combinations of toxicity levels, evidence statuses, and source types
"""

import json
import requests
import sys
from typing import Dict, Any

API_BASE = "http://127.0.0.1:8000"

def load_test_data() -> Dict[str, Any]:
    """Load test scenarios from JSON file"""
    with open("test_sample_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def test_single_comment(comment_text: str, test_id: int, expected: Dict[str, str]) -> Dict[str, Any]:
    """Test a single comment and compare with expected output"""
    try:
        response = requests.post(
            f"{API_BASE}/analyze-evidence",
            json={"text": comment_text},
            timeout=30
        )

        if response.status_code != 200:
            return {
                "test_id": test_id,
                "status": "ERROR",
                "error": f"HTTP {response.status_code}",
                "comment": comment_text[:50]
            }

        data = response.json()

        # Extract actual values
        toxicity_color = data.get("toxicity_color", "unknown")
        evidence_status = data.get("status", "unknown")
        badge_color = data.get("badge_color", "unknown")
        toxicity_scores = data.get("toxicity_scores", {})
        toxic_score = toxicity_scores.get("toxic", 0.0)

        # Determine tone label
        tone_labels = {
            "red": "Strong language",
            "yellow": "Slightly strong language",
            "green": "Positive tone"
        }
        actual_tone = tone_labels.get(toxicity_color, "Unknown")

        # Determine evidence label
        evidence_labels = {
            "Verified": "Verifiable evidence present",
            "Unverified": "Unverifiable evidence",
            "Mixed": "Partially verifiable evidence",
            "None": "No evidence",
            "Evidence present, unverified": "Unverifiable evidence"
        }
        actual_evidence = evidence_labels.get(evidence_status, evidence_status)

        # Determine source label
        evidence_data = data.get("evidence", {})
        results = evidence_data.get("results", [])
        urls = evidence_data.get("urls", [])

        if len(urls) == 0:
            actual_source = "URL is not present"
        else:
            verified_urls = [r for r in results if r.get("verified", False)]
            if verified_urls:
                # Show first verified URL
                first_verified = verified_urls[0]
                actual_source = first_verified.get("final_url") or first_verified.get("normalized_url") or first_verified.get("input_url", "URL present")
            else:
                actual_source = "URL is not verified"

        # Check if results match expectations (partial matching)
        checks = {
            "badge_color_match": badge_color == expected.get("badge_color"),
            "toxicity_color_match": toxicity_color in expected.get("toxicity_level", ""),
            "evidence_status_match": evidence_status == expected.get("evidence_status"),
        }

        all_passed = all(checks.values())

        return {
            "test_id": test_id,
            "status": "PASS" if all_passed else "FAIL",
            "comment": comment_text[:80] + "..." if len(comment_text) > 80 else comment_text,
            "expected": {
                "badge_color": expected.get("badge_color"),
                "toxicity_level": expected.get("toxicity_level"),
                "evidence_status": expected.get("evidence_status")
            },
            "actual": {
                "badge_color": badge_color,
                "toxicity_color": toxicity_color,
                "toxicity_score": round(toxic_score, 3),
                "evidence_status": evidence_status,
                "tone_label": actual_tone,
                "evidence_label": actual_evidence,
                "source_label": actual_source[:100] + "..." if len(actual_source) > 100 else actual_source
            },
            "checks": checks
        }

    except requests.exceptions.ConnectionError:
        return {
            "test_id": test_id,
            "status": "ERROR",
            "error": "Cannot connect to API - is the server running?",
            "comment": comment_text[:50]
        }
    except Exception as e:
        return {
            "test_id": test_id,
            "status": "ERROR",
            "error": str(e),
            "comment": comment_text[:50]
        }

def print_result(result: Dict[str, Any]):
    """Pretty print a test result"""
    status_symbol = {
        "PASS": "✓",
        "FAIL": "✗",
        "ERROR": "⚠"
    }

    symbol = status_symbol.get(result["status"], "?")
    print(f"\n{symbol} Test #{result['test_id']}: {result['status']}")
    print(f"   Comment: {result['comment']}")

    if result["status"] == "ERROR":
        print(f"   Error: {result.get('error', 'Unknown error')}")
        return

    print(f"\n   Expected:")
    for key, value in result.get("expected", {}).items():
        print(f"      {key}: {value}")

    print(f"\n   Actual:")
    for key, value in result.get("actual", {}).items():
        print(f"      {key}: {value}")

    if result["status"] == "FAIL":
        print(f"\n   Failed checks:")
        for check, passed in result.get("checks", {}).items():
            if not passed:
                print(f"      ✗ {check}")

def run_all_tests():
    """Run all test cases and generate report"""
    print("=" * 80)
    print("TrustLens Badge Logic Test Suite")
    print("=" * 80)

    # Check API health
    try:
        health = requests.get(f"{API_BASE}/health", timeout=5)
        if health.status_code != 200:
            print("⚠ Warning: API health check failed")
    except:
        print("✗ ERROR: Cannot connect to API. Please start the server with:")
        print("  cd api && uvicorn main:app --reload --port 8000")
        return

    print("✓ API is running\n")

    # Load test data
    test_data = load_test_data()
    test_cases = test_data.get("test_cases", [])

    print(f"Running {len(test_cases)} test cases...\n")

    results = []
    for test_case in test_cases:
        test_id = test_case["id"]
        category = test_case["category"]
        comment = test_case["comment"]
        expected = test_case["expected_output"]

        print(f"Testing #{test_id}: {category}... ", end="", flush=True)
        result = test_single_comment(comment, test_id, expected)
        results.append(result)
        print(result["status"])

    # Print detailed results
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)

    for result in results:
        print_result(result)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"✓ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"✗ Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"⚠ Errors: {errors} ({errors/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed!")
    elif failed > 0:
        print(f"\n⚠ {failed} test(s) failed - review results above")

    if errors > 0:
        print(f"\n⚠ {errors} test(s) had errors - check API connectivity and logs")

    # Save results to file
    output_file = "test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    run_all_tests()
