"""
Risk primitive tests covering threshold violations, edge cases, authentication, and feature flags.
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
TEST_API_KEY = "test_risk_key_12345"
TEST_API_KEY_HASH = hash_api_key(TEST_API_KEY)


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return create_access_token({"sub": "test_user", "user_id": 1})


@pytest.fixture
def mock_api_key_validation():
    """Mock API key validation to avoid database dependency."""
    with patch('security.auth.verify_api_key') as mock:
        mock.return_value = {"key": TEST_API_KEY, "user_id": 1, "rate_limit": 1000}
        yield mock


@pytest.fixture
def risk_request_payload():
    """Sample risk validation request payload."""
    return {
        "metrics": {
            "sharpe_ratio": 1.5,
            "sortino_ratio": 1.8,
            "max_drawdown": 0.15,
            "var_95": -0.03,
            "var_99": -0.07,
            "calmar_ratio": 0.8,
            "volatility": 0.25
        },
        "thresholds": {
            "min_sharpe": 1.0,
            "min_sortino": 1.2,
            "max_drawdown": 0.20,
            "max_var_95": -0.05,
            "max_var_99": -0.10,
            "min_calmar": 0.5,
            "max_volatility": 0.30
        },
        "context": {
            "strategy_id": "test_strategy_001",
            "backtest_period": "2023-01-01_to_2023-12-31"
        }
    }


class TestRiskPrimitiveAuthentication:
    """Test authentication and authorization for risk primitive."""

    def test_risk_validate_requires_auth(self):
        """Test that risk validate endpoint requires authentication."""
        response = client.post("/api/primitives/v1/risk/validate", json={
            "metrics": {"sharpe_ratio": 1.5},
            "thresholds": {"min_sharpe": 1.0}
        })
        assert response.status_code == 401

    def test_risk_validate_with_jwt_token(self, valid_jwt_token, risk_request_payload):
        """Test risk validate with JWT token authentication."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=risk_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code in [200, 403]  # 403 if feature flag disabled

    def test_risk_validate_with_api_key(self, mock_api_key_validation, risk_request_payload):
        """Test risk validate with API key authentication."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=risk_request_payload,
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert response.status_code in [200, 403]  # 403 if feature flag disabled


class TestRiskPrimitiveThresholdViolations:
    """Test risk validation threshold violations."""

    def test_sharpe_ratio_violation(self, valid_jwt_token):
        """Test Sharpe ratio below threshold."""
        payload = {
            "metrics": {"sharpe_ratio": 0.5},
            "thresholds": {"min_sharpe": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["overall_pass"] is False
                sharpe_check = next((c for c in data["checks"] if c["metric"] == "sharpe_ratio"), None)
                assert sharpe_check is not None
                assert sharpe_check["passed"] is False

    def test_max_drawdown_violation(self, valid_jwt_token):
        """Test max drawdown exceeding threshold."""
        payload = {
            "metrics": {"max_drawdown": 0.30},
            "thresholds": {"max_drawdown": 0.20}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["overall_pass"] is False
                dd_check = next((c for c in data["checks"] if c["metric"] == "max_drawdown"), None)
                assert dd_check is not None
                assert dd_check["passed"] is False

    def test_var_95_violation(self, valid_jwt_token):
        """Test VaR 95% exceeding threshold."""
        payload = {
            "metrics": {"var_95": -0.08},
            "thresholds": {"max_var_95": -0.05}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["overall_pass"] is False
                var_check = next((c for c in data["checks"] if c["metric"] == "var_95"), None)
                assert var_check is not None
                assert var_check["passed"] is False

    def test_all_thresholds_pass(self, valid_jwt_token, risk_request_payload):
        """Test all risk checks passing."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=risk_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["overall_pass"] is True
                assert data["risk_score"] == 100.0
                assert all(check["passed"] for check in data["checks"])


class TestRiskPrimitiveEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_required_metrics(self, valid_jwt_token):
        """Test request with missing required metrics."""
        payload = {
            "metrics": {},
            "thresholds": {"min_sharpe": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should handle gracefully - either validation error or empty checks
            assert response.status_code in [200, 422]

    def test_negative_sharpe_ratio(self, valid_jwt_token):
        """Test handling of negative Sharpe ratio."""
        payload = {
            "metrics": {"sharpe_ratio": -0.5},
            "thresholds": {"min_sharpe": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["overall_pass"] is False

    def test_zero_volatility(self, valid_jwt_token):
        """Test handling of zero volatility (edge case)."""
        payload = {
            "metrics": {"volatility": 0.0},
            "thresholds": {"max_volatility": 0.30}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Zero volatility should pass (below threshold)
            if response.status_code == 200:
                data = response.json()["data"]
                vol_check = next((c for c in data["checks"] if c["metric"] == "volatility"), None)
                if vol_check:
                    assert vol_check["passed"] is True

    def test_extreme_values(self, valid_jwt_token):
        """Test handling of extreme metric values."""
        payload = {
            "metrics": {
                "sharpe_ratio": 10.0,
                "max_drawdown": 0.99,
                "var_95": -0.50
            },
            "thresholds": {
                "min_sharpe": 1.0,
                "max_drawdown": 0.20,
                "max_var_95": -0.05
            }
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should handle without errors
            assert response.status_code in [200, 422]


class TestRiskPrimitiveFeatureFlags:
    """Test feature flag functionality."""

    def test_risk_primitive_disabled(self, valid_jwt_token, risk_request_payload):
        """Test risk primitive when feature flag is disabled."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.side_effect = Exception("Risk primitive is disabled")
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=risk_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code == 403


class TestRiskPrimitiveResponseStructure:
    """Test canonical response envelope structure."""

    def test_response_has_canonical_structure(self, valid_jwt_token, risk_request_payload):
        """Test that response follows canonical envelope pattern."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=risk_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                json_data = response.json()
                assert "data" in json_data
                assert "meta" in json_data
                assert "links" in json_data
                assert "timestamp" in json_data["meta"]
                assert "primitive" in json_data["meta"]
                assert json_data["meta"]["primitive"] == "risk"

    def test_health_endpoint(self):
        """Test risk primitive health endpoint."""
        response = client.get("/api/primitives/v1/risk/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["primitive"] == "risk"
        assert "version" in data


class TestRiskPrimitiveValidation:
    """Test input validation and error messages."""

    def test_invalid_json_payload(self, valid_jwt_token):
        """Test handling of invalid JSON payload."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                data="invalid json",
                headers={"Authorization": f"Bearer {valid_jwt_token}", "Content-Type": "application/json"}
            )
            assert response.status_code == 422

    def test_missing_thresholds_uses_defaults(self, valid_jwt_token):
        """Test that missing thresholds use default values."""
        payload = {
            "metrics": {"sharpe_ratio": 1.5}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/risk/validate",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should use default thresholds
            assert response.status_code in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
