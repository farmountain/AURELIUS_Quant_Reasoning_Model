"""
Test harness for AURELIUS API primitives.

Provides contract testing framework to ensure:
- Response schemas match OpenAPI specification
- Authentication and rate limiting work correctly
- Error handling follows canonical format
- Performance meets SLA requirements (<200ms p95)
"""
import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
import time


class PrimitiveTestHarness:
    """
    Base test harness for primitive API contract tests.
    
    Provides assertions for:
    - Canonical envelope structure
    - Error response format
    - Rate limit headers
    - Performance requirements
    """
    
    def __init__(self, client: TestClient):
        self.client = client
    
    def assert_canonical_envelope(self, response_json: Dict[str, Any]):
        """Assert response follows canonical envelope schema."""
        assert "data" in response_json, "Response must have 'data' field"
        assert "meta" in response_json, "Response must have 'meta' field"
        
        meta = response_json["meta"]
        assert "version" in meta, "Meta must have 'version' field"
        assert "timestamp" in meta, "Meta must have 'timestamp' field"
        assert "request_id" in meta, "Meta must have 'request_id' field"
        
        # Optional links field
        if "links" in response_json:
            assert isinstance(response_json["links"], dict)
    
    def assert_error_response(self, response_json: Dict[str, Any]):
        """Assert error response follows standard format."""
        assert "error" in response_json, "Error response must have 'error' field"
        assert "meta" in response_json, "Error response must have 'meta' field"
        
        error = response_json["error"]
        assert "code" in error, "Error must have 'code' field"
        assert "message" in error, "Error must have 'message' field"
    
    def assert_rate_limit_headers(self, response):
        """Assert rate limit headers are present."""
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def assert_performance_sla(self, latency_ms: float, threshold_ms: float = 200):
        """Assert response time meets SLA."""
        assert latency_ms < threshold_ms, \
            f"Response time {latency_ms}ms exceeds SLA threshold {threshold_ms}ms"
    
    def test_authentication_required(self, endpoint: str, method: str = "POST"):
        """Test that endpoint requires authentication."""
        if method == "POST":
            response = self.client.post(endpoint)
        elif method == "GET":
            response = self.client.get(endpoint)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        assert response.status_code == 401
        self.assert_error_response(response.json())
    
    def test_api_key_auth(
        self,
        endpoint: str,
        api_key: str,
        payload: Dict[str, Any] = None,
        method: str = "POST"
    ):
        """Test API key authentication."""
        headers = {"X-API-Key": api_key}
        
        if method == "POST":
            response = self.client.post(endpoint, json=payload, headers=headers)
        elif method == "GET":
            response = self.client.get(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Should not be 401 with valid key
        assert response.status_code != 401
        
        # Should have rate limit headers
        self.assert_rate_limit_headers(response)
        
        return response
    
    def test_jwt_auth(
        self,
        endpoint: str,
        jwt_token: str,
        payload: Dict[str, Any] = None,
        method: str = "POST"
    ):
        """Test JWT token authentication."""
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        if method == "POST":
            response = self.client.post(endpoint, json=payload, headers=headers)
        elif method == "GET":
            response = self.client.get(endpoint, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        # Should not be 401 with valid token
        assert response.status_code != 401
        
        # Should have rate limit headers
        self.assert_rate_limit_headers(response)
        
        return response
    
    def test_rate_limiting(
        self,
        endpoint: str,
        api_key: str,
        limit: int = 1000
    ):
        """Test that rate limiting works."""
        headers = {"X-API-Key": api_key}
        
        # Make requests until rate limit hit
        for i in range(limit + 10):
            response = self.client.post(endpoint, json={}, headers=headers)
            
            if response.status_code == 429:
                # Rate limit exceeded
                assert i >= limit, f"Rate limit hit too early at request {i}"
                self.assert_error_response(response.json())
                self.assert_rate_limit_headers(response)
                return
        
        pytest.fail("Rate limit was not enforced")
    
    def measure_latency(
        self,
        endpoint: str,
        api_key: str,
        payload: Dict[str, Any] = None,
        iterations: int = 10
    ) -> Dict[str, float]:
        """
        Measure endpoint latency over multiple requests.
        
        Returns:
            Dictionary with avg, p50, p95, p99 latencies in milliseconds
        """
        headers = {"X-API-Key": api_key}
        latencies = []
        
        for _ in range(iterations):
            start = time.time()
            response = self.client.post(endpoint, json=payload, headers=headers)
            latency_ms = (time.time() - start) * 1000
            
            assert response.status_code < 500, "Server error during latency test"
            latencies.append(latency_ms)
        
        latencies.sort()
        return {
            "avg_ms": sum(latencies) / len(latencies),
            "p50_ms": latencies[len(latencies) // 2],
            "p95_ms": latencies[int(len(latencies) * 0.95)],
            "p99_ms": latencies[int(len(latencies) * 0.99)]
        }


# Fixtures for test harness
@pytest.fixture
def primitive_test_harness(client: TestClient) -> PrimitiveTestHarness:
    """Provide primitive test harness fixture."""
    return PrimitiveTestHarness(client)


@pytest.fixture
def test_api_key() -> str:
    """Provide test API key fixture."""
    # In production, this would be a real API key from setup
    return "ak_test_key_for_integration_tests"


@pytest.fixture
def test_jwt_token() -> str:
    """Provide test JWT token fixture."""
    # In production, this would be generated from auth flow
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"
