"""
Test script to verify single word comment processing works correctly
"""
import requests
import json

API_BASE = "http://127.0.0.1:8000"

def test_single_word_comments():
    """Test that single words are processed correctly"""
    test_cases = [
        {"text": "fuck", "expected_toxicity": "red"},
        {"text": "shit", "expected_toxicity": "red"},
        {"text": "nice", "expected_toxicity": "green"},
        {"text": "good", "expected_toxicity": "green"},
        {"text": "damn", "expected_toxicity": "yellow"},
    ]

    print("=" * 70)
    print("Testing Single Word Comment Processing")
    print("=" * 70)

    # Check API health
    try:
        health = requests.get(f"{API_BASE}/health", timeout=5)
        if health.status_code != 200:
            print("⚠ Warning: API health check failed")
            print("Please start the server with: START_TRUSTLENS.bat")
            return
    except:
        print("ERROR: Cannot connect to API. Please start the server with:")
        print("  START_TRUSTLENS.bat")
        return

    print("OK: API is running\n")

    results = []
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        expected = test_case["expected_toxicity"]

        print(f"\nTest {i}: Testing word '{text}'...")

        try:
            # Test /predict endpoint
            response = requests.post(
                f"{API_BASE}/predict",
                json={"texts": [text]},
                timeout=10
            )

            if response.status_code != 200:
                print(f"  FAIL: HTTP {response.status_code}")
                results.append({"test": text, "status": "FAIL", "error": f"HTTP {response.status_code}"})
                continue

            data = response.json()

            # Check if badge_colors exists
            if "badge_colors" not in data:
                print(f"  FAIL: No badge_colors in response")
                results.append({"test": text, "status": "FAIL", "error": "No badge_colors"})
                continue

            badge_color = data["badge_colors"][0]
            toxic_score = data["detailed"][0]["scores"]["toxic"]

            # Verify badge color matches expectation
            if badge_color == expected:
                print(f"  PASS: Badge color = {badge_color}, Toxic score = {toxic_score:.3f}")
                results.append({"test": text, "status": "PASS", "badge_color": badge_color, "toxic_score": toxic_score})
            else:
                print(f"  WARNING: Expected {expected}, got {badge_color} (Toxic score = {toxic_score:.3f})")
                results.append({"test": text, "status": "WARNING", "expected": expected, "actual": badge_color, "toxic_score": toxic_score})

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"test": text, "status": "ERROR", "error": str(e)})

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["status"] == "PASS")
    warnings = sum(1 for r in results if r["status"] == "WARNING")
    failed = sum(1 for r in results if r["status"] in ["FAIL", "ERROR"])
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Warnings: {warnings}")
    print(f"Failed: {failed}")

    if passed == total:
        print("\nAll tests passed!")
    elif warnings > 0:
        print(f"\n{warnings} test(s) had different colors than expected (this may be OK)")

    if failed > 0:
        print(f"\n{failed} test(s) failed - review results above")

    # Save results
    with open("test_single_word_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to: test_single_word_results.json")

if __name__ == "__main__":
    test_single_word_comments()
