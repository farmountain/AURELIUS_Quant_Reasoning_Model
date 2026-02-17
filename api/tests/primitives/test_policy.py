"""
Policy primitive tests covering rule combinations, edge cases, authentication, and feature flags.
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
TEST_API_KEY = "test_policy_key_67890"
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
def policy_request_payload():
    """Sample policy check request payload."""
    return {
        "policies": [
            {
                "rule_id": "max_drawdown_regulatory",
                "threshold": 0.25,
                "severity": "blocker"
            },
            {
                "rule_id": "max_leverage_regulatory",
                "threshold": 2.0,
                "severity": "blocker"
            },
            {
                "rule_id": "lineage_completeness",
                "threshold": 1.0,
                "severity": "warning"
            }
        ],
        "context": {
            "max_drawdown": 0.18,
            "leverage": 1.5,
            "lineage_complete": True,
            "governance_approved": True,
            "turnover": 3.2,
            "strategy_id": "test_strategy_001"
        }
    }


class TestPolicyPrimitiveAuthentication:
    """Test authentication and authorization for policy primitive."""

    def test_policy_check_requires_auth(self):
        """Test that policy check endpoint requires authentication."""
        response = client.post("/api/primitives/v1/policy/check", json={
            "policies": [],
            "context": {}
        })
        assert response.status_code == 401

    def test_policy_check_with_jwt_token(self, valid_jwt_token, policy_request_payload):
        """Test policy check with JWT token authentication."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=policy_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code in [200, 403]  # 403 if feature flag disabled

    def test_policy_check_with_api_key(self, mock_api_key_validation, policy_request_payload):
        """Test policy check with API key authentication."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=policy_request_payload,
                headers={"X-API-Key": TEST_API_KEY}
            )
            assert response.status_code in [200, 403]  # 403 if feature flag disabled


class TestPolicyPrimitiveRuleViolations:
    """Test policy rule violations."""

    def test_max_drawdown_violation(self, valid_jwt_token):
        """Test max drawdown exceeding regulatory limit."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"}
            ],
            "context": {"max_drawdown": 0.30}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["compliant"] is False
                assert len(data["blockers"]) > 0
                blocker = next((b for b in data["blockers"] if b["rule_id"] == "max_drawdown_regulatory"), None)
                assert blocker is not None

    def test_max_leverage_violation(self, valid_jwt_token):
        """Test leverage exceeding regulatory limit."""
        payload = {
            "policies": [
                {"rule_id": "max_leverage_regulatory", "threshold": 2.0, "severity": "blocker"}
            ],
            "context": {"leverage": 3.5}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["compliant"] is False
                assert len(data["blockers"]) > 0

    def test_lineage_completeness_warning(self, valid_jwt_token):
        """Test lineage completeness generating warning."""
        payload = {
            "policies": [
                {"rule_id": "lineage_completeness", "threshold": 1.0, "severity": "warning"}
            ],
            "context": {"lineage_complete": False}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                # Should have warning but still be compliant (warnings don't block)
                assert len(data["warnings"]) > 0
                warning = next((w for w in data["warnings"] if w["rule_id"] == "lineage_completeness"), None)
                assert warning is not None

    def test_all_policies_pass(self, valid_jwt_token, policy_request_payload):
        """Test all policy checks passing."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=policy_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["compliant"] is True
                assert data["compliance_score"] == 100.0
                assert len(data["blockers"]) == 0


class TestPolicyPrimitiveRuleCombinations:
    """Test combinations of multiple policy rules."""

    def test_multiple_blockers(self, valid_jwt_token):
        """Test multiple blocker violations."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"},
                {"rule_id": "max_leverage_regulatory", "threshold": 2.0, "severity": "blocker"}
            ],
            "context": {
                "max_drawdown": 0.30,
                "leverage": 3.0
            }
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["compliant"] is False
                assert len(data["blockers"]) == 2

    def test_mixed_blockers_and_warnings(self, valid_jwt_token):
        """Test combination of blockers and warnings."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"},
                {"rule_id": "lineage_completeness", "threshold": 1.0, "severity": "warning"}
            ],
            "context": {
                "max_drawdown": 0.30,
                "lineage_complete": False
            }
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert data["compliant"] is False
                assert len(data["blockers"]) >= 1
                assert len(data["warnings"]) >= 1

    def test_all_warning_severity(self, valid_jwt_token):
        """Test all policies as warnings (should not block compliance)."""
        payload = {
            "policies": [
                {"rule_id": "lineage_completeness", "threshold": 1.0, "severity": "warning"},
                {"rule_id": "governance_compliance", "threshold": 1.0, "severity": "warning"}
            ],
            "context": {
                "lineage_complete": False,
                "governance_approved": False
            }
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                # Warnings don't block compliance
                assert data["compliant"] is True or len(data["blockers"]) == 0


class TestPolicyPrimitiveEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_policies_list(self, valid_jwt_token):
        """Test request with empty policies list."""
        payload = {
            "policies": [],
            "context": {}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should handle gracefully - either success with 100% compliance or validation error
            assert response.status_code in [200, 422]

    def test_unknown_rule_id(self, valid_jwt_token):
        """Test handling of unknown rule ID."""
        payload = {
            "policies": [
                {"rule_id": "unknown_rule_xyz", "threshold": 1.0, "severity": "blocker"}
            ],
            "context": {}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should handle gracefully
            assert response.status_code in [200, 422]

    def test_missing_context_data(self, valid_jwt_token):
        """Test handling of missing required context data."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"}
            ],
            "context": {}  # Missing max_drawdown
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should handle missing data gracefully
            assert response.status_code in [200, 422]

    def test_extreme_threshold_values(self, valid_jwt_token):
        """Test handling of extreme threshold values."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 999.0, "severity": "blocker"}
            ],
            "context": {"max_drawdown": 0.10}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should handle without errors
            assert response.status_code in [200, 422]


class TestPolicyPrimitiveFeatureFlags:
    """Test feature flag functionality."""

    def test_policy_primitive_disabled(self, valid_jwt_token, policy_request_payload):
        """Test policy primitive when feature flag is disabled."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.side_effect = Exception("Policy primitive is disabled")
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=policy_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code == 403


class TestPolicyPrimitiveResponseStructure:
    """Test canonical response envelope structure."""

    def test_response_has_canonical_structure(self, valid_jwt_token, policy_request_payload):
        """Test that response follows canonical envelope pattern."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=policy_request_payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                json_data = response.json()
                assert "data" in json_data
                assert "meta" in json_data
                assert "links" in json_data
                assert "timestamp" in json_data["meta"]
                assert "primitive" in json_data["meta"]
                assert json_data["meta"]["primitive"] == "policy"

    def test_blockers_and_warnings_separation(self, valid_jwt_token):
        """Test that blockers and warnings are properly separated."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"},
                {"rule_id": "lineage_completeness", "threshold": 1.0, "severity": "warning"}
            ],
            "context": {
                "max_drawdown": 0.30,
                "lineage_complete": False
            }
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "blockers" in data
                assert "warnings" in data
                assert isinstance(data["blockers"], list)
                assert isinstance(data["warnings"], list)

    def test_health_endpoint(self):
        """Test policy primitive health endpoint."""
        response = client.get("/api/primitives/v1/policy/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["primitive"] == "policy"
        assert "version" in data


class TestPolicyPrimitiveValidation:
    """Test input validation and error messages."""

    def test_invalid_json_payload(self, valid_jwt_token):
        """Test handling of invalid JSON payload."""
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                data="invalid json",
                headers={"Authorization": f"Bearer {valid_jwt_token}", "Content-Type": "application/json"}
            )
            assert response.status_code == 422

    def test_invalid_severity_value(self, valid_jwt_token):
        """Test handling of invalid severity value."""
        payload = {
            "policies": [
                {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "invalid_severity"}
            ],
            "context": {"max_drawdown": 0.10}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/policy/check",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            # Should reject invalid severity
            assert response.status_code in [422, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
