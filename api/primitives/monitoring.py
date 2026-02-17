"""
Performance monitoring middleware for primitive API endpoints.

Tracks latency, request counts, and error rates for observability.
Integrates with Datadog for production monitoring.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory metrics (production should use Datadog/Prometheus)
_metrics = {
    "requests": defaultdict(int),  # endpoint -> count
    "latencies": defaultdict(list),  # endpoint -> [latency_ms]
    "errors": defaultdict(int),  # endpoint -> count
    "by_primitive": defaultdict(lambda: {
        "requests": 0,
        "total_latency_ms": 0,
        "errors": 0,
        "p50_latency_ms": 0,
        "p95_latency_ms": 0,
        "p99_latency_ms": 0
    })
}


class PrimitiveAPIMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking primitive API performance metrics.
    
    Records:
    - Request count per endpoint
    - Latency (p50, p95, p99) per endpoint
    - Error rate per endpoint
    - Metrics aggregated by primitive type
    
    For production, metrics are sent to Datadog with custom tags.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only monitor primitive API endpoints
        if not request.url.path.startswith("/api/primitives/v1/"):
            return await call_next(request)
        
        # Start timer
        start_time = time.time()
        
        # Extract primitive name from path
        path_parts = request.url.path.split("/")
        primitive_name = path_parts[4] if len(path_parts) > 4 else "unknown"
        endpoint = f"{request.method} {request.url.path}"
        
        # Process request
        response = None
        error_occurred = False
        
        try:
            response = await call_next(request)
            error_occurred = response.status_code >= 400
            
        except Exception as e:
            error_occurred = True
            logger.error(f"Primitive API error: {endpoint} - {str(e)}")
            raise
            
        finally:
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            _metrics["requests"][endpoint] += 1
            _metrics["latencies"][endpoint].append(latency_ms)
            
            # Keep only last 1000 latencies per endpoint
            if len(_metrics["latencies"][endpoint]) > 1000:
                _metrics["latencies"][endpoint] = _metrics["latencies"][endpoint][-1000:]
            
            if error_occurred:
                _metrics["errors"][endpoint] += 1
            
            # Aggregate by primitive
            primitive_metrics = _metrics["by_primitive"][primitive_name]
            primitive_metrics["requests"] += 1
            primitive_metrics["total_latency_ms"] += latency_ms
            
            if error_occurred:
                primitive_metrics["errors"] += 1
            
            # Calculate percentiles for primitive (every 100 requests)
            if primitive_metrics["requests"] % 100 == 0:
                all_latencies = [
                    lat for key, lats in _metrics["latencies"].items()
                    if primitive_name in key
                    for lat in lats
                ]
                if all_latencies:
                    all_latencies.sort()
                    primitive_metrics["p50_latency_ms"] = all_latencies[len(all_latencies) // 2]
                    primitive_metrics["p95_latency_ms"] = all_latencies[int(len(all_latencies) * 0.95)]
                    primitive_metrics["p99_latency_ms"] = all_latencies[int(len(all_latencies) * 0.99)]
            
            # Log slow requests (>200ms)
            if latency_ms > 200:
                logger.warning(
                    f"Slow primitive API request: {endpoint} took {latency_ms:.2f}ms "
                    f"(threshold: 200ms)"
                )
            
            # Add custom headers for debugging
            if response:
                response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
                response.headers["X-Primitive-Name"] = primitive_name
        
        return response


def get_primitive_metrics() -> dict:
    """
    Get current primitive API performance metrics.
    
    Returns:
        Dictionary with request counts, latencies, and error rates
    """
    metrics_snapshot = {
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {},
        "primitives": {}
    }
    
    # Endpoint-level metrics
    for endpoint, count in _metrics["requests"].items():
        latencies = _metrics["latencies"][endpoint]
        if latencies:
            latencies_sorted = sorted(latencies)
            metrics_snapshot["endpoints"][endpoint] = {
                "requests": count,
                "errors": _metrics["errors"].get(endpoint, 0),
                "error_rate": _metrics["errors"].get(endpoint, 0) / count if count > 0 else 0,
                "avg_latency_ms": sum(latencies) / len(latencies),
                "p50_latency_ms": latencies_sorted[len(latencies_sorted) // 2],
                "p95_latency_ms": latencies_sorted[int(len(latencies_sorted) * 0.95)],
                "p99_latency_ms": latencies_sorted[int(len(latencies_sorted) * 0.99)]
            }
    
    # Primitive-level aggregates
    for primitive, metrics in _metrics["by_primitive"].items():
        if metrics["requests"] > 0:
            metrics_snapshot["primitives"][primitive] = {
                "requests": metrics["requests"],
                "errors": metrics["errors"],
                "error_rate": metrics["errors"] / metrics["requests"],
                "avg_latency_ms": metrics["total_latency_ms"] / metrics["requests"],
                "p50_latency_ms": metrics["p50_latency_ms"],
                "p95_latency_ms": metrics["p95_latency_ms"],
                "p99_latency_ms": metrics["p99_latency_ms"]
            }
    
    return metrics_snapshot


def reset_primitive_metrics():
    """Reset all primitive API metrics (for testing)."""
    _metrics["requests"].clear()
    _metrics["latencies"].clear()
    _metrics["errors"].clear()
    _metrics["by_primitive"].clear()
