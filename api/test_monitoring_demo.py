"""
Demo script to test the integrated performance monitoring.
Simulates comment processing and displays real-time metrics.
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evidence_monitored import (
    analyze_comments_monitored,
    get_performance_stats,
    print_performance_summary
)

# Sample test comments
test_comments = [
    {
        "comment_id": "c1",
        "text": "According to a study published in Nature, this approach is effective. See https://www.nature.com/articles/example"
    },
    {
        "comment_id": "c2",
        "text": "Research shows that 78% of users prefer this method."
    },
    {
        "comment_id": "c3",
        "text": "I think this is great. Just my personal opinion, no sources needed."
    },
    {
        "comment_id": "c4",
        "text": "Multiple sources confirm this: https://www.bbc.com/news and https://www.reuters.com/article"
    },
    {
        "comment_id": "c5",
        "text": "Dr. Johnson from Stanford University suggests this is the correct approach (Johnson et al. 2023)."
    },
    {
        "comment_id": "c6",
        "text": "Check out this blog post: https://example-blog.com/post"
    },
    {
        "comment_id": "c7",
        "text": "The data clearly indicates a significant improvement over baseline methods."
    },
    {
        "comment_id": "c8",
        "text": "According to research from MIT, this has been proven effective. https://mit.edu/research/paper"
    }
]


def main():
    print("="*80)
    print("  PERFORMANCE MONITORING DEMO")
    print("="*80)
    print(f"\nProcessing {len(test_comments)} test comments...")
    print("This will demonstrate real-time performance tracking.\n")

    # Process comments with monitoring
    results = analyze_comments_monitored(test_comments)

    # Display results
    print("\n" + "="*80)
    print("  ANALYSIS RESULTS")
    print("="*80)

    for result in results:
        print(f"\n[{result['comment_id']}] Status: {result['status']}")
        print(f"  Evidence Present: {result['evidence_present']}")
        print(f"  URLs Found: {len(result['urls'])}")
        print(f"  Verified: {result['verified']}")
        print(f"  TL2: {result['TL2_tooltip']}")

    # Display performance metrics
    print_performance_summary()

    # Get detailed stats
    print("\n" + "="*80)
    print("  DETAILED PERFORMANCE METRICS")
    print("="*80)

    stats = get_performance_stats()

    print(f"\nVerification Statistics:")
    print(f"  Total URLs Verified: {stats['total_urls_verified']}")
    print(f"  Successful: {stats['successful_verifications']}")
    print(f"  Failed: {stats['failed_verifications']}")
    print(f"  Success Rate: {stats['verification_success_rate']:.2f}%")

    print(f"\nThroughput:")
    print(f"  Overall: {stats['overall_throughput_comments_per_sec']:.2f} comments/sec")

    print("\n✓ Demo complete!")
    print("\nThe monitoring is now integrated into your main.py.")
    print("Every comment processed will be tracked automatically.\n")


if __name__ == "__main__":
    main()
