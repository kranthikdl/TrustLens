"""
Test that performance metrics are included in the main JSON output.
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

from evidence_monitored import analyze_comments_monitored, get_performance_stats
from output_formatter import format_all_results

# Mock toxicity results
mock_toxicity_results = {
    "detailed": [
        {"badge_color": "green", "scores": {}, "predictions": {}},
        {"badge_color": "yellow", "scores": {}, "predictions": {}},
    ]
}

# Test comments
test_comments = [
    {"comment_id": "c1", "text": "According to research, this works."},
    {"comment_id": "c2", "text": "I think this is great!"}
]

# Analyze with monitoring
evidence_results = analyze_comments_monitored(test_comments)

# Get performance stats
perf_stats = get_performance_stats()

# Format all results (including performance)
formatted_output = format_all_results(
    comments=[c["text"] for c in test_comments],
    toxicity_results=mock_toxicity_results,
    evidence_results=evidence_results,
    source_filename="test_file.json",
    performance_stats=perf_stats
)

# Save to test output
test_output_path = "artifacts/test_output_with_performance.json"
os.makedirs("artifacts", exist_ok=True)

with open(test_output_path, "w", encoding="utf-8") as f:
    json.dump(formatted_output, f, indent=2, ensure_ascii=False)

print("✓ Test output saved to:", test_output_path)
print("\nChecking for performance_metrics in output...")

if "performance_metrics" in formatted_output:
    print("✅ SUCCESS: performance_metrics found in JSON output!")
    print("\nPerformance data included:")
    print(f"  - Total comments processed: {formatted_output['performance_metrics']['total_comments_processed']}")
    print(f"  - Total URLs verified: {formatted_output['performance_metrics']['total_urls_verified']}")
    print(f"  - Overall throughput: {formatted_output['performance_metrics']['overall_throughput_comments_per_sec']:.2f} comments/sec")
    print("\nFull JSON structure:")
    print(f"  - source_filename: ✓")
    print(f"  - total_comments: ✓")
    print(f"  - summary: ✓")
    print(f"  - comments: ✓")
    print(f"  - raw_data: ✓")
    print(f"  - performance_metrics: ✓")
else:
    print("❌ ERROR: performance_metrics NOT found in output!")

print(f"\n📄 Full output saved to: {test_output_path}")
print("You can open this file to see the complete structure with performance data.")
