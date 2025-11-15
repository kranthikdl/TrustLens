"""
Evidence Model Performance Testing Script
Tests latency and response rate for the evidence detection system.
"""
import sys
import os
import io
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evidence import (
    analyze_comment,
    detect_pattern_based_evidence,
    extract_urls_from_text,
    verify_and_classify,
    normalize_url
)

class PerformanceTester:
    def __init__(self):
        self.results = {
            "pattern_detection": [],
            "url_extraction": [],
            "url_verification": [],
            "full_analysis": []
        }

    def print_header(self, title: str):
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)

    def measure_latency(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        return result, latency

    def test_pattern_detection(self, test_cases: List[str], iterations: int = 10):
        """Test pattern-based evidence detection performance."""
        self.print_header("Testing Pattern Detection Performance")

        latencies = []
        for i in range(iterations):
            for text in test_cases:
                _, latency = self.measure_latency(detect_pattern_based_evidence, text)
                latencies.append(latency)

        self.results["pattern_detection"] = latencies

        print(f"\nTested {len(test_cases)} cases × {iterations} iterations = {len(latencies)} total operations")
        print(f"Average Latency: {statistics.mean(latencies):.3f} ms")
        print(f"Median Latency: {statistics.median(latencies):.3f} ms")
        print(f"Min Latency: {min(latencies):.3f} ms")
        print(f"Max Latency: {max(latencies):.3f} ms")
        print(f"Std Deviation: {statistics.stdev(latencies):.3f} ms" if len(latencies) > 1 else "N/A")

        # Calculate throughput (operations per second)
        avg_latency_sec = statistics.mean(latencies) / 1000
        throughput = 1 / avg_latency_sec if avg_latency_sec > 0 else 0
        print(f"Throughput: {throughput:.2f} operations/second")

    def test_url_extraction(self, test_cases: List[str], iterations: int = 10):
        """Test URL extraction performance."""
        self.print_header("Testing URL Extraction Performance")

        latencies = []
        total_urls_found = 0

        for i in range(iterations):
            for text in test_cases:
                result, latency = self.measure_latency(extract_urls_from_text, text)
                latencies.append(latency)
                total_urls_found += len(result)

        self.results["url_extraction"] = latencies

        print(f"\nTested {len(test_cases)} cases × {iterations} iterations = {len(latencies)} total operations")
        print(f"Total URLs Extracted: {total_urls_found}")
        print(f"Average Latency: {statistics.mean(latencies):.3f} ms")
        print(f"Median Latency: {statistics.median(latencies):.3f} ms")
        print(f"Min Latency: {min(latencies):.3f} ms")
        print(f"Max Latency: {max(latencies):.3f} ms")
        print(f"Std Deviation: {statistics.stdev(latencies):.3f} ms" if len(latencies) > 1 else "N/A")

        avg_latency_sec = statistics.mean(latencies) / 1000
        throughput = 1 / avg_latency_sec if avg_latency_sec > 0 else 0
        print(f"Throughput: {throughput:.2f} operations/second")

    def test_url_verification(self, urls: List[str], iterations: int = 3):
        """Test URL verification performance (network-dependent, fewer iterations)."""
        self.print_header("Testing URL Verification Performance")
        print("⚠️  Note: This test makes actual network requests and may be slow")

        latencies = []
        success_count = 0
        failure_count = 0

        for i in range(iterations):
            print(f"\nIteration {i+1}/{iterations}...")
            for url in urls:
                print(f"  Testing: {url}", end=" ")
                result, latency = self.measure_latency(verify_and_classify, url)
                latencies.append(latency)

                if result.get("verified"):
                    success_count += 1
                    print(f"✓ ({latency:.0f} ms)")
                else:
                    failure_count += 1
                    print(f"✗ ({latency:.0f} ms) - {result.get('reason', 'unknown')}")

        self.results["url_verification"] = latencies

        print(f"\nTested {len(urls)} URLs × {iterations} iterations = {len(latencies)} total operations")
        print(f"Successful Verifications: {success_count}")
        print(f"Failed Verifications: {failure_count}")
        print(f"\nLatency Statistics:")
        print(f"Average Latency: {statistics.mean(latencies):.3f} ms")
        print(f"Median Latency: {statistics.median(latencies):.3f} ms")
        print(f"Min Latency: {min(latencies):.3f} ms")
        print(f"Max Latency: {max(latencies):.3f} ms")
        print(f"Std Deviation: {statistics.stdev(latencies):.3f} ms" if len(latencies) > 1 else "N/A")

        avg_latency_sec = statistics.mean(latencies) / 1000
        throughput = 1 / avg_latency_sec if avg_latency_sec > 0 else 0
        print(f"Throughput: {throughput:.2f} operations/second")

    def test_full_analysis(self, comments: List[Dict[str, str]], iterations: int = 5):
        """Test full comment analysis performance."""
        self.print_header("Testing Full Comment Analysis Performance")

        latencies = []

        for i in range(iterations):
            print(f"Iteration {i+1}/{iterations}...")
            for comment in comments:
                _, latency = self.measure_latency(
                    analyze_comment,
                    comment["id"],
                    comment["text"]
                )
                latencies.append(latency)

        self.results["full_analysis"] = latencies

        print(f"\nTested {len(comments)} comments × {iterations} iterations = {len(latencies)} total operations")
        print(f"Average Latency: {statistics.mean(latencies):.3f} ms")
        print(f"Median Latency: {statistics.median(latencies):.3f} ms")
        print(f"Min Latency: {min(latencies):.3f} ms")
        print(f"Max Latency: {max(latencies):.3f} ms")
        print(f"Std Deviation: {statistics.stdev(latencies):.3f} ms" if len(latencies) > 1 else "N/A")

        avg_latency_sec = statistics.mean(latencies) / 1000
        throughput = 1 / avg_latency_sec if avg_latency_sec > 0 else 0
        print(f"Throughput: {throughput:.2f} operations/second")

    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        self.print_header("Performance Summary Report")

        print(f"\nTest Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "-"*80)

        for test_name, latencies in self.results.items():
            if not latencies:
                continue

            print(f"\n{test_name.upper().replace('_', ' ')}:")
            print(f"  Operations: {len(latencies)}")
            print(f"  Avg Latency: {statistics.mean(latencies):.3f} ms")
            print(f"  Median: {statistics.median(latencies):.3f} ms")
            print(f"  Min: {min(latencies):.3f} ms")
            print(f"  Max: {max(latencies):.3f} ms")

            avg_latency_sec = statistics.mean(latencies) / 1000
            throughput = 1 / avg_latency_sec if avg_latency_sec > 0 else 0
            print(f"  Throughput: {throughput:.2f} ops/sec")

            # Performance rating
            avg_ms = statistics.mean(latencies)
            if test_name == "url_verification":
                # Network calls are expected to be slower
                if avg_ms < 500:
                    rating = "EXCELLENT"
                elif avg_ms < 2000:
                    rating = "GOOD"
                elif avg_ms < 5000:
                    rating = "ACCEPTABLE"
                else:
                    rating = "SLOW"
            else:
                # Local operations should be fast
                if avg_ms < 1:
                    rating = "EXCELLENT"
                elif avg_ms < 5:
                    rating = "GOOD"
                elif avg_ms < 20:
                    rating = "ACCEPTABLE"
                else:
                    rating = "SLOW"

            print(f"  Performance: {rating}")

        print("\n" + "-"*80)


def main():
    tester = PerformanceTester()

    print("="*80)
    print("  EVIDENCE MODEL PERFORMANCE TEST SUITE")
    print("="*80)
    print("\nThis script will test latency and response rate for:")
    print("  1. Pattern-based evidence detection")
    print("  2. URL extraction from text")
    print("  3. URL verification and classification")
    print("  4. Full comment analysis")

    # Test data
    pattern_test_cases = [
        "According to a study published last year, 75% of users prefer this approach.",
        "Research shows that this method is more effective than traditional approaches.",
        "The data shows a clear correlation between these two factors.",
        "I think this is the best approach. In my experience, it works well.",
        "This finding was published in a peer-reviewed journal last month.",
        "Dr. Johnson, a professor at Stanford, suggests this is the correct approach.",
        "Studies found that 68% of participants showed improvement.",
        "According to recent research conducted at MIT, this is the best solution."
    ]

    url_test_cases = [
        "Check out this article: https://www.example.com/article",
        "Multiple sources: https://news.bbc.com and https://www.reuters.com/news",
        "According to https://nature.com/article, this is proven.",
        "No URLs in this text, just plain opinion.",
        "Visit www.example.org for more information about this topic.",
        "https://arxiv.org/abs/1234.5678 has the full research paper."
    ]

    verification_urls = [
        "https://www.google.com",
        "https://www.wikipedia.org",
        "https://www.github.com"
    ]

    full_analysis_comments = [
        {"id": "c1", "text": "According to a study, this works well. See https://example.com"},
        {"id": "c2", "text": "Research shows clear benefits in this approach."},
        {"id": "c3", "text": "I think this is good, no evidence needed."},
        {"id": "c4", "text": "Multiple sources confirm: https://bbc.com and https://reuters.com"},
        {"id": "c5", "text": "Data indicates a 45% improvement (Smith et al. 2023)."}
    ]

    # Run tests
    try:
        # Test 1: Pattern Detection (fast, many iterations)
        tester.test_pattern_detection(pattern_test_cases, iterations=50)

        # Test 2: URL Extraction (fast, many iterations)
        tester.test_url_extraction(url_test_cases, iterations=50)

        # Test 3: URL Verification (slow, few iterations due to network calls)
        print("\n⚠️  Running URL verification test (makes network requests)...")
        tester.test_url_verification(verification_urls, iterations=3)

        # Test 4: Full Analysis (moderate speed)
        tester.test_full_analysis(full_analysis_comments, iterations=10)

        # Generate summary
        tester.generate_summary_report()

        print("\n✓ Performance testing complete!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        tester.generate_summary_report()
    except Exception as e:
        print(f"\n\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
