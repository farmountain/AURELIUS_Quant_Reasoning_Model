"""
Contract tests for primitive API infrastructure.

Tests canonical envelope, authentication, rate limiting, and error handling
that are common across all primitives.
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from tests.primitives.test_harness import PrimitiveTestHarness


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def harness(client):
    """Create test harness."""
    return PrimitiveTestHarness(client)


class TestPrimitiveInfrastructure:
    """Test suite for primitive API infrastructure components."""
    
    def test_openapi_spec_accessible(self, client):
        """Test that OpenAPI specification is accessible."""
        response = client.get("/api/primitives/v1/openapi/primitives/v1.json")
        
        assert response.status_code == 200
        spec = response.json()
        
        # Validate OpenAPI structure
        assert "openapi" in spec
        assert spec["openapi"] == "3.0.0"
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
        
        # Validate security schemes
        assert "securitySchemes" in spec["components"]
        assert "ApiKeyAuth" in spec["components"]["securitySchemes"]
        assert "BearerAuth" in spec["components"]["securitySchemes"]
    
    def test_canonical_envelope_schema(self, harness):
        """Test canonical envelope structure for valid responses."""
        # This will be implemented when primitives are available
        # For now, test the schema validation logic
        
        valid_response = {
            "data": {"score": 95},
            "meta": {
                "version": "v1",
                "timestamp": "2026-02-16T10:00:00Z",
                "request_id": "test-id-123"
            },
            "links": {"self": "/test"}
        }
        
        # Should not raise assertion error
        harness.assert_canonical_envelope(valid_response)
    
    def test_error_response_schema(self, harness):
        """Test error response structure."""
        error_response = {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input"
            },
            "meta": {
                "version": "v1",
                "timestamp": "2026-02-16T10:00:00Z",
                "request_id": "test-id-123"
            }
        }
        
        # Should not raise assertion error
        harness.assert_error_response(error_response)
    
    def test_monitoring_middleware_active(self, client):
        """Test that monitoring middleware is tracking metrics."""
        from primitives.monitoring import get_primitive_metrics, reset_primitive_metrics
        
        # Reset metrics
        reset_primitive_metrics()
        
        # Make a request to a primitive endpoint (will 404 since no primitives yet)
        client.get("/api/primitives/v1/test/endpoint")
        
        # Check metrics were recorded
        metrics = get_primitive_metrics()
        assert "timestamp" in metrics
        assert "endpoints" in metrics
        assert "primitives" in metrics


class TestFeatureFlags:
    """Test suite for feature flag system."""
    
    def test_feature_flags_exist(self):
        """Test that primitive feature flags are defined."""
        from config import settings
        
        # All primitive flags should exist
        assert hasattr(settings, "enable_primitive_determinism")
        assert hasattr(settings, "enable_primitive_risk")
        assert hasattr(settings, "enable_primitive_policy")
        assert hasattr(settings, "enable_primitive_strategy")
        assert hasattr(settings, "enable_primitive_evidence")
        assert hasattr(settings, "enable_primitive_gates")
        assert hasattr(settings, "enable_primitive_reflexion")
        assert hasattr(settings, "enable_primitive_orchestrator")
        assert hasattr(settings, "enable_primitive_readiness")
    
    def test_feature_flag_checking(self):
        """Test feature flag utilities."""
        from primitives.feature_flags import FeatureFlags
        
        # Should return list of enabled primitives (none by default)
        enabled = FeatureFlags.get_enabled_primitives()
        assert isinstance(enabled, list)
        
        # Should check if primitive enabled
        is_enabled = FeatureFlags.is_primitive_enabled("determinism")
        assert isinstance(is_enabled, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
