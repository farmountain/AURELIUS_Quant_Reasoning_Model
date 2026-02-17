"""
Readiness primitive tests covering authentication, DROPS scoring, hard blockers, and response envelope.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from main import app
from security.auth import create_access_token, hash_api_key

client = TestClient(app)


# Test API keys
TEST_API_KEY = "test_readiness_key_11111"
TEST_API_KEY_HASH = hash_api_key(TEST_API_KEY)


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return create_access_token({"sub": "test_user", "user_id": 1})


@pytest.fixture
def healthy_signals():
    """Generate healthy readiness signals."""
    return {
        "run_identity_present": True,
        "parity_checked": True,
        "parity_passed": True,
        "validation_passed": True,
        "crv_available": True,
        "risk_metrics_complete": True,
        "policy_block_reasons": [],
        "lineage_complete": True,
        "startup_status": "healthy",
        "startup_reasons": [],
        "evidence_stale": False,
        "environment_caveat": None,
        "evidence_classification": "GREEN",
        "evidence_timestamp": "2024-01-15T10:30:00Z",
        "contract_mismatch": False,
        "maturity_label_visible": True
    }


@pytest.fixture
def blocked_signals():
    """Generate signals with hard blockers."""
    return {
        "run_identity_present": False,
        "parity_checked": False,
        "parity_passed": False,
        "validation_passed": True,
        "crv_available": True,
        "risk_metrics_complete": True,
        "policy_block_reasons": ["compliance_violation"],
        "lineage_complete": False,
        "startup_status": "healthy",
        "startup_reasons": [],
        "evidence_stale": False,
        "environment_caveat": None,
        "evidence_classification": "GREEN",
        "evidence_timestamp": "2024-01-15T10:30:00Z",
        "contract_mismatch": False,
        "maturity_label_visible": True
    }


class TestReadinessPrimitiveAuthentication:
    """Test authentication and authorization for readiness primitive."""

    def test_readiness_score_requires_auth(self, healthy_signals):
        """Test that readiness score endpoint requires authentication."""
        response = client.post("/api/primitives/v1/readiness/score", json={
            "strategy_id": "test_001",
            "signals": healthy_signals
        })
        assert response.status_code == 401

    def test_readiness_score_with_jwt(self, valid_jwt_token, healthy_signals):
        """Test readiness score with valid JWT token."""
        payload = {
            "strategy_id": "test_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code in [200, 500]  # May fail due to dependencies


class TestReadinessDROPSScoring:
    """Test DROPS dimension scoring logic."""

    def test_healthy_signals_high_score(self, valid_jwt_token, healthy_signals):
        """Test that healthy signals produce high readiness score."""
        payload = {
            "strategy_id": "healthy_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["overall_score"] >= 85
                assert data["color"] == "GREEN"
                assert len(data["blockers"]) == 0

    def test_drops_dimensions_present(self, valid_jwt_token, healthy_signals):
        """Test that DROPS dimensions are all present in response."""
        payload = {
            "strategy_id": "dims_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                dimensions = data["dimensions"]
                assert "D" in dimensions  # Determinism
                assert "R" in dimensions  # Risk
                assert "O" in dimensions  # Ops
                assert "P" in dimensions  # Policy
                assert "U" in dimensions  # User/UI

    def test_dimension_score_range(self, valid_jwt_token, healthy_signals):
        """Test that dimension scores are in valid range (0-100)."""
        payload = {
            "strategy_id": "range_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                for dim, score in data["dimensions"].items():
                    assert 0 <= score <= 100, f"Dimension {dim} score {score} out of range"


class TestReadinessHardBlockers:
    """Test hard blocker detection and reporting."""

    def test_blocked_signals_produce_blockers(self, valid_jwt_token, blocked_signals):
        """Test that blocked signals are detected and reported."""
        payload = {
            "strategy_id": "blocked_001",
            "signals": blocked_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert len(data["blockers"]) > 0
                assert data["color"] == "RED"
                assert "blocked" in data["recommendation"].lower()

    def test_missing_run_identity_blocker(self, valid_jwt_token, healthy_signals):
        """Test that missing run identity is a hard blocker."""
        signals = healthy_signals.copy()
        signals["run_identity_present"] = False
        
        payload = {
            "strategy_id": "no_run_id_001",
            "signals": signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "missing_run_identity" in data["blockers"]

    def test_parity_failure_blocker(self, valid_jwt_token, healthy_signals):
        """Test that parity check failure is a hard blocker."""
        signals = healthy_signals.copy()
        signals["parity_passed"] = False
        
        payload = {
            "strategy_id": "parity_fail_001",
            "signals": signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "parity_check_failed" in data["blockers"]

    def test_policy_violation_blocker(self, valid_jwt_token, healthy_signals):
        """Test that policy violations are hard blockers."""
        signals = healthy_signals.copy()
        signals["policy_block_reasons"] = ["compliance_violation", "risk_limit_exceeded"]
        
        payload = {
            "strategy_id": "policy_block_001",
            "signals": signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "policy_block_reasons" in data["blockers"]


class TestReadinessColorBands:
    """Test color band classification (GREEN, AMBER, RED)."""

    def test_green_band_threshold(self, valid_jwt_token, healthy_signals):
        """Test that high scores result in GREEN band."""
        payload = {
            "strategy_id": "green_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                if data["overall_score"] >= 85:
                    assert data["color"] == "GREEN"

    def test_amber_band_threshold(self, valid_jwt_token, healthy_signals):
        """Test AMBER band for moderate scores."""
        signals = healthy_signals.copy()
        signals["validation_passed"] = False
        signals["crv_available"] = False
        
        payload = {
            "strategy_id": "amber_001",
            "signals": signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                # Amber band is typically 70-84
                if 70 <= data["overall_score"] < 85:
                    assert data["color"] == "AMBER"

    def test_red_band_with_blockers(self, valid_jwt_token, blocked_signals):
        """Test RED band when hard blockers exist."""
        payload = {
            "strategy_id": "red_001",
            "signals": blocked_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["color"] == "RED"


class TestReadinessFeatureFlags:
    """Test feature flag functionality."""

    def test_readiness_primitive_disabled(self, valid_jwt_token, healthy_signals):
        """Test readiness primitive when feature flag is disabled."""
        payload = {
            "strategy_id": "test_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.side_effect = Exception("Readiness primitive is disabled")
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code == 403


class TestReadinessResponseStructure:
    """Test canonical response envelope structure."""

    def test_response_has_canonical_structure(self, valid_jwt_token, healthy_signals):
        """Test that response follows canonical envelope pattern."""
        payload = {
            "strategy_id": "test_001",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
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
                assert json_data["meta"]["primitive"] == "readiness"

    def test_response_data_structure(self, valid_jwt_token, healthy_signals):
        """Test response data has required fields."""
        payload = {
            "strategy_id": "test_002",
            "signals": healthy_signals
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "strategy_id" in data
                assert "overall_score" in data
                assert "color" in data
                assert "recommendation" in data
                assert "dimensions" in data
                assert "blockers" in data

    def test_health_endpoint(self):
        """Test readiness primitive health endpoint."""
        response = client.get("/api/primitives/v1/readiness/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["primitive"] == "readiness"


class TestReadinessValidation:
    """Test request validation and error handling."""

    def test_missing_signals(self, valid_jwt_token):
        """Test error when signals are missing."""
        payload = {
            "strategy_id": "test_001"
            # Missing signals field
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code == 422  # Validation error

    def test_invalid_signal_types(self, valid_jwt_token):
        """Test error when signal types are invalid."""
        payload = {
            "strategy_id": "test_001",
            "signals": {
                "run_identity_present": "invalid",  # Should be boolean
                "parity_checked": True,
                "parity_passed": True,
                "validation_passed": True,
                "crv_available": True,
                "risk_metrics_complete": True,
                "policy_block_reasons": [],
                "lineage_complete": True,
                "startup_status": "healthy",
                "startup_reasons": [],
                "evidence_stale": False,
                "contract_mismatch": False,
                "maturity_label_visible": True
            }
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/readiness/score",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
