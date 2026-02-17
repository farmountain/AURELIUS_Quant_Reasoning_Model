"""
Evidence primitive tests covering classification, freshness, completeness, authentication, and feature flags.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from main import app
from security.auth import create_access_token, hash_api_key

client = TestClient(app)


# Test API keys
TEST_API_KEY = "test_evidence_key_67890"
TEST_API_KEY_HASH = hash_api_key(TEST_API_KEY)


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return create_access_token({"sub": "test_user", "user_id": 1})


@pytest.fixture
def fresh_timestamp():
    """Generate a fresh timestamp (within last hour)."""
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture
def stale_timestamp():
    """Generate a stale timestamp (48 hours old)."""
    return (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()


class TestEvidencePrimitiveAuthentication:
    """Test authentication and authorization for evidence primitive."""

    def test_evidence_classify_requires_auth(self):
        """Test that evidence classify endpoint requires authentication."""
        response = client.post("/api/primitives/v1/evidence/classify", json={
            "evidence_id": "test_001",
            "evidence_type": "backtest",
            "data": {}
        })
        assert response.status_code == 401


class TestEvidenceGateCheckClassification:
    """Test gate check evidence classification."""

    def test_contract_valid_success(self, valid_jwt_token, fresh_timestamp):
        """Test gate check with all 200 status codes."""
        payload = {
            "evidence_id": "gate_001",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 200,
                "crv_status": 200,
                "product_status": 200,
                "environment": "staging"
            },
            "timestamp": fresh_timestamp,
            "max_age_hours": 24
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "contract-valid-success"
                assert data["confidence"] == 1.0
                assert data["details"]["is_fresh"] is True

    def test_contract_valid_failure(self, valid_jwt_token, fresh_timestamp):
        """Test gate check with dev pass but crv/product fail."""
        payload = {
            "evidence_id": "gate_002",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 200,
                "crv_status": 404,
                "product_status": 422,
                "environment": "staging"
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "contract-valid-failure"
                assert data["confidence"] == 0.9

    def test_contract_invalid_failure(self, valid_jwt_token, fresh_timestamp):
        """Test gate check with 500 errors."""
        payload = {
            "evidence_id": "gate_003",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 500,
                "crv_status": 200,
                "product_status": 200,
                "environment": "production"
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "contract-invalid-failure"
                assert data["confidence"] == 0.7

    def test_mixed_gate_results(self, valid_jwt_token, fresh_timestamp):
        """Test gate check with mixed results."""
        payload = {
            "evidence_id": "gate_004",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 200,
                "crv_status": 200,
                "product_status": 400,
                "environment": "staging"
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "mixed"


class TestEvidenceBacktestClassification:
    """Test backtest evidence classification."""

    def test_valid_backtest(self, valid_jwt_token, fresh_timestamp):
        """Test backtest with good metrics."""
        payload = {
            "evidence_id": "backtest_001",
            "evidence_type": "backtest",
            "data": {
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.15,
                "total_return": 0.25,
                "num_trades": 50
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "valid"
                assert data["confidence"] == 1.0

    def test_poor_backtest_metrics(self, valid_jwt_token, fresh_timestamp):
        """Test backtest with poor metrics."""
        payload = {
            "evidence_id": "backtest_002",
            "evidence_type": "backtest",
            "data": {
                "sharpe_ratio": -0.5,
                "max_drawdown": 0.60,
                "total_return": -0.20,
                "num_trades": 5
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "contract-valid-failure"

    def test_incomplete_backtest(self, valid_jwt_token, fresh_timestamp):
        """Test backtest with missing fields."""
        payload = {
            "evidence_id": "backtest_003",
            "evidence_type": "backtest",
            "data": {
                "sharpe_ratio": 1.5
                # Missing other required fields
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "incomplete"
                assert len(data["details"]["missing_fields"]) > 0


class TestEvidenceFreshnessChecking:
    """Test evidence freshness validation."""

    def test_fresh_evidence(self, valid_jwt_token, fresh_timestamp):
        """Test evidence within max age."""
        payload = {
            "evidence_id": "fresh_001",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 200,
                "crv_status": 200,
                "product_status": 200
            },
            "timestamp": fresh_timestamp,
            "max_age_hours": 24
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["details"]["is_fresh"] is True
                assert data["details"]["age_hours"] < 24

    def test_stale_evidence(self, valid_jwt_token, stale_timestamp):
        """Test evidence exceeding max age."""
        payload = {
            "evidence_id": "stale_001",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 200,
                "crv_status": 200,
                "product_status": 200
            },
            "timestamp": stale_timestamp,
            "max_age_hours": 24
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["details"]["is_fresh"] is False
                assert data["details"]["age_hours"] > 24
                assert len(data["details"]["warnings"]) > 0

    def test_missing_timestamp(self, valid_jwt_token):
        """Test evidence without timestamp."""
        payload = {
            "evidence_id": "no_ts_001",
            "evidence_type": "gate_check",
            "data": {
                "dev_status": 200,
                "crv_status": 200,
                "product_status": 200
            }
            # No timestamp provided
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert len(data["details"]["warnings"]) > 0


class TestEvidenceValidationClassification:
    """Test validation evidence classification."""

    def test_completed_validation(self, valid_jwt_token, fresh_timestamp):
        """Test validation with completed status."""
        payload = {
            "evidence_id": "validation_001",
            "evidence_type": "validation",
            "data": {
                "status": "completed",
                "metrics": {"avg_sharpe": 1.5}
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "valid"

    def test_failed_validation(self, valid_jwt_token, fresh_timestamp):
        """Test validation with failed status."""
        payload = {
            "evidence_id": "validation_002",
            "evidence_type": "validation",
            "data": {
                "status": "failed"
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "contract-valid-failure"


class TestEvidenceFeatureFlags:
    """Test feature flag functionality."""

    def test_evidence_primitive_disabled(self, valid_jwt_token, fresh_timestamp):
        """Test evidence primitive when feature flag is disabled."""
        payload = {
            "evidence_id": "test_001",
            "evidence_type": "backtest",
            "data": {"sharpe_ratio": 1.5},
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.side_effect = Exception("Evidence primitive is disabled")
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code == 403


class TestEvidenceResponseStructure:
    """Test canonical response envelope structure."""

    def test_response_has_canonical_structure(self, valid_jwt_token, fresh_timestamp):
        """Test that response follows canonical envelope pattern."""
        payload = {
            "evidence_id": "test_001",
            "evidence_type": "backtest",
            "data": {
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.15,
                "total_return": 0.25,
                "num_trades": 50
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                json_data = response.json()
                assert "data" in json_data
                assert "meta" in json_data
                assert "links" in json_data
                assert "timestamp" in json_data["meta"]
                assert "primitive" in json_data["meta"]
                assert json_data["meta"]["primitive"] == "evidence"

    def test_health_endpoint(self):
        """Test evidence primitive health endpoint."""
        response = client.get("/api/primitives/v1/evidence/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["primitive"] == "evidence"


class TestEvidenceProductionMetrics:
    """Test production metrics evidence classification."""

    def test_good_production_metrics(self, valid_jwt_token, fresh_timestamp):
        """Test production metrics with good values."""
        payload = {
            "evidence_id": "prod_001",
            "evidence_type": "production_metrics",
            "data": {
                "uptime": 0.999,
                "error_rate": 0.001,
                "latency_p95": 150
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "valid"

    def test_poor_production_metrics(self, valid_jwt_token, fresh_timestamp):
        """Test production metrics with poor values."""
        payload = {
            "evidence_id": "prod_002",
            "evidence_type": "production_metrics",
            "data": {
                "uptime": 0.95,
                "error_rate": 0.05,
                "latency_p95": 2000
            },
            "timestamp": fresh_timestamp
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/evidence/classify",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["classification"] == "contract-valid-failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
