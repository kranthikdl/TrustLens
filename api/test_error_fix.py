"""
Test that the evidence detection handles malformed URLs gracefully
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evidence import extract_urls_from_text, analyze_comment

print("="*70)
print("  Testing Error Handling for Malformed URLs")
print("="*70)

# Test cases with potentially problematic URLs
test_cases = [
    {
        "name": "Normal URL",
        "text": "Check this out: https://www.example.com/article"
    },
    {
        "name": "Very long URL (should be filtered)",
        "text": f"Look at this: https://example.com/{'a' * 2100}"
    },
    {
        "name": "URL with underscores in markdown",
        "text": "[Link](https://open.substack.com/pub/jenesaii/p/when-the-doctor-spoke?r=5rixnk&utm\\_medium=ios)"
    },
    {
        "name": "Multiple URLs with markdown",
        "text": "Check [this](https://example.com) and also https://normal-site.com/page"
    },
    {
        "name": "Empty or malformed domain",
        "text": "Visit https:// or http://.com/page"
    }
]

print("\n[1/2] Testing URL Extraction...")
for i, test in enumerate(test_cases, 1):
    print(f"\n  Test {i}: {test['name']}")
    print(f"  Text: {test['text'][:80]}{'...' if len(test['text']) > 80 else ''}")

    try:
        urls = extract_urls_from_text(test['text'])
        print(f"  ✓ Extracted {len(urls)} URLs: {urls if urls else '(none)'}")
    except Exception as e:
        print(f"  ✗ ERROR: {type(e).__name__}: {e}")

print("\n[2/2] Testing Full Comment Analysis...")
# Test with a real problematic comment
problematic_comment = """
I recommend checking out this article:
[https://open.substack.com/pub/jenesaii/p/when-the-doctor-spoke-the-world-stopped-7b4?r=5rixnk&utm\\_medium=ios](https://open.substack.com/pub/jenesaii/p/when-the-doctor-spoke-the-world-stopped-7b4?r=5rixnk&utm_medium=ios)

Also see: https://www.example.com and maybe https://""" + ("x" * 300) + """.com/toolong
"""

print("\n  Analyzing comment with multiple URL formats...")
try:
    result = analyze_comment("test_problematic", problematic_comment)
    print(f"  ✓ Analysis completed successfully")
    print(f"    Status: {result['status']}")
    print(f"    URLs found: {len(result['urls'])}")
    print(f"    Evidence present: {result['evidence_present']}")
    print(f"    TL2 Tooltip: {result['TL2_tooltip']}")

    if result['results']:
        print(f"\n  URL Verification Results:")
        for url_result in result['results']:
            print(f"    - {url_result['input_url'][:60]}...")
            print(f"      Verified: {url_result['verified']}, Reason: {url_result['reason']}")
except Exception as e:
    print(f"  ✗ FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("  Test Complete - Checking for errors...")
print("="*70)
print("\n  If you see this message without crashes, the fix is working! ✓")
print()
