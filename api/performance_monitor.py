"""
Real-time Performance Monitor for Evidence Analysis
Tracks latency, response rate, and throughput for all evidence processing operations.
"""
import time
import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import deque


class PerformanceMonitor:
    """
    Monitor performance metrics for evidence analysis operations.
    Tracks latency, throughput, and generates real-time statistics.
    """

    def __init__(self, window_size: int = 100, enable_logging: bool = True):
        """
        Initialize the performance monitor.

        Args:
            window_size: Number of recent operations to keep for rolling stats
            enable_logging: Whether to log metrics to file
        """
        self.window_size = window_size
        self.enable_logging = enable_logging

        # Store recent latencies for rolling statistics
        self.pattern_detection_latencies = deque(maxlen=window_size)
        self.url_extraction_latencies = deque(maxlen=window_size)
        self.url_verification_latencies = deque(maxlen=window_size)
        self.full_analysis_latencies = deque(maxlen=window_size)

        # Counters
        self.total_comments_processed = 0
        self.total_urls_verified = 0
        self.successful_verifications = 0
        self.failed_verifications = 0

        # Session start time
        self.session_start = time.time()

        # Logs directory
        self.logs_dir = Path(__file__).parent / "performance_logs"
        if enable_logging:
            self.logs_dir.mkdir(exist_ok=True)

    def measure_operation(self, operation_type: str):
        """
        Context manager to measure operation latency.

        Usage:
            with monitor.measure_operation("pattern_detection") as timer:
                result = detect_patterns(text)
        """
        return OperationTimer(self, operation_type)

    def record_latency(self, operation_type: str, latency_ms: float):
        """Record a latency measurement."""
        if operation_type == "pattern_detection":
            self.pattern_detection_latencies.append(latency_ms)
        elif operation_type == "url_extraction":
            self.url_extraction_latencies.append(latency_ms)
        elif operation_type == "url_verification":
            self.url_verification_latencies.append(latency_ms)
        elif operation_type == "full_analysis":
            self.full_analysis_latencies.append(latency_ms)

    def record_comment_processed(self):
        """Increment the total comments processed counter."""
        self.total_comments_processed += 1

    def record_url_verification(self, success: bool):
        """Record a URL verification attempt."""
        self.total_urls_verified += 1
        if success:
            self.successful_verifications += 1
        else:
            self.failed_verifications += 1

    def get_stats(self, operation_type: str) -> Dict[str, Any]:
        """Get statistics for a specific operation type."""
        if operation_type == "pattern_detection":
            latencies = list(self.pattern_detection_latencies)
        elif operation_type == "url_extraction":
            latencies = list(self.url_extraction_latencies)
        elif operation_type == "url_verification":
            latencies = list(self.url_verification_latencies)
        elif operation_type == "full_analysis":
            latencies = list(self.full_analysis_latencies)
        else:
            return {}

        if not latencies:
            return {
                "operation": operation_type,
                "sample_size": 0,
                "avg_latency_ms": 0,
                "median_latency_ms": 0,
                "min_latency_ms": 0,
                "max_latency_ms": 0,
                "throughput_ops_per_sec": 0
            }

        avg_latency = statistics.mean(latencies)

        return {
            "operation": operation_type,
            "sample_size": len(latencies),
            "avg_latency_ms": round(avg_latency, 3),
            "median_latency_ms": round(statistics.median(latencies), 3),
            "min_latency_ms": round(min(latencies), 3),
            "max_latency_ms": round(max(latencies), 3),
            "std_dev_ms": round(statistics.stdev(latencies), 3) if len(latencies) > 1 else 0,
            "throughput_ops_per_sec": round(1000 / avg_latency, 2) if avg_latency > 0 else 0
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all operations."""
        session_duration = time.time() - self.session_start

        stats = {
            "timestamp": datetime.now().isoformat(),
            "session_duration_seconds": round(session_duration, 2),
            "total_comments_processed": self.total_comments_processed,
            "total_urls_verified": self.total_urls_verified,
            "successful_verifications": self.successful_verifications,
            "failed_verifications": self.failed_verifications,
            "verification_success_rate": round(
                (self.successful_verifications / self.total_urls_verified * 100)
                if self.total_urls_verified > 0 else 0,
                2
            ),
            "overall_throughput_comments_per_sec": round(
                self.total_comments_processed / session_duration,
                2
            ) if session_duration > 0 else 0,
            "operations": {
                "pattern_detection": self.get_stats("pattern_detection"),
                "url_extraction": self.get_stats("url_extraction"),
                "url_verification": self.get_stats("url_verification"),
                "full_analysis": self.get_stats("full_analysis")
            }
        }

        return stats

    def log_stats(self, filename: Optional[str] = None):
        """Save current statistics to a JSON file."""
        if not self.enable_logging:
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"

        filepath = self.logs_dir / filename
        stats = self.get_all_stats()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def print_summary(self):
        """Print a human-readable summary of current performance metrics."""
        stats = self.get_all_stats()

        print("\n" + "="*80)
        print("  EVIDENCE ANALYSIS PERFORMANCE SUMMARY")
        print("="*80)
        print(f"\nSession Duration: {stats['session_duration_seconds']:.2f} seconds")
        print(f"Total Comments Processed: {stats['total_comments_processed']}")
        print(f"Total URLs Verified: {stats['total_urls_verified']}")
        print(f"Verification Success Rate: {stats['verification_success_rate']:.2f}%")
        print(f"Overall Throughput: {stats['overall_throughput_comments_per_sec']:.2f} comments/sec")

        print("\nOperation-Level Metrics:")
        print("-" * 80)

        for op_name, op_stats in stats['operations'].items():
            if op_stats['sample_size'] == 0:
                continue

            print(f"\n{op_name.upper().replace('_', ' ')}:")
            print(f"  Sample Size: {op_stats['sample_size']}")
            print(f"  Avg Latency: {op_stats['avg_latency_ms']:.3f} ms")
            print(f"  Median: {op_stats['median_latency_ms']:.3f} ms")
            print(f"  Range: {op_stats['min_latency_ms']:.3f} - {op_stats['max_latency_ms']:.3f} ms")
            print(f"  Throughput: {op_stats['throughput_ops_per_sec']:.2f} ops/sec")

        print("\n" + "="*80)

    def reset(self):
        """Reset all metrics (useful for testing or starting fresh)."""
        self.pattern_detection_latencies.clear()
        self.url_extraction_latencies.clear()
        self.url_verification_latencies.clear()
        self.full_analysis_latencies.clear()

        self.total_comments_processed = 0
        self.total_urls_verified = 0
        self.successful_verifications = 0
        self.failed_verifications = 0

        self.session_start = time.time()


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(self, monitor: PerformanceMonitor, operation_type: str):
        self.monitor = monitor
        self.operation_type = operation_type
        self.start_time = None
        self.latency_ms = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.perf_counter()
        self.latency_ms = (end_time - self.start_time) * 1000  # Convert to ms
        self.monitor.record_latency(self.operation_type, self.latency_ms)
        return False  # Don't suppress exceptions


# Global monitor instance (singleton pattern)
_global_monitor: Optional[PerformanceMonitor] = None


def get_monitor(window_size: int = 100, enable_logging: bool = True) -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(window_size, enable_logging)
    return _global_monitor


def reset_monitor():
    """Reset the global monitor instance."""
    global _global_monitor
    if _global_monitor is not None:
        _global_monitor.reset()
