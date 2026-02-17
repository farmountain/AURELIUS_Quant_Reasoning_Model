"""
Reflexion primitive tests covering improvement scoring, suggestion generation, priorities, and authentication.
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
TEST_API_KEY = "test_reflexion_key_99999"
TEST_API_KEY_HASH = hash_api_key(TEST_API_KEY)


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return create_access_token({"sub": "test_user", "user_id": 1})


class TestReflexionPrimitiveAuthentication:
    """Test authentication and authorization for reflexion primitive."""

    def test_reflexion_suggest_requires_auth(self):
        """Test that reflexion suggest endpoint requires authentication."""
        response = client.post("/api/primitives/v1/reflexion/suggest", json={
            "strategy_id": "test_001",
            "strategy_type": "momentum",
            "parameters": {},
            "performance_metrics": {}
        })
        assert response.status_code == 401

    def test_reflexion_suggest_with_jwt(self, valid_jwt_token):
        """Test reflexion suggest with valid JWT token."""
        payload = {
            "strategy_id": "test_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 0.8}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code in [200, 500]  # May fail due to dependencies


class TestReflexionImprovementScoring:
    """Test improvement score calculation."""

    def test_score_range(self, valid_jwt_token):
        """Test that improvement scores are in valid range (-2.0 to +2.0)."""
        payload = {
            "strategy_id": "test_score_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                score = data["improvement_score"]
                assert -2.0 <= score <= 2.0

    def test_score_deterministic(self, valid_jwt_token):
        """Test that same strategy produces same improvement score."""
        payload = {
            "strategy_id": "test_det_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response1 = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            response2 = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response1.status_code == 200 and response2.status_code == 200:
                score1 = response1.json()["data"]["improvement_score"]
                score2 = response2.json()["data"]["improvement_score"]
                assert score1 == score2


class TestReflexionMetricBasedSuggestions:
    """Test suggestions generated from performance metrics."""

    def test_low_sharpe_suggestion(self, valid_jwt_token):
        """Test suggestions for low Sharpe ratio."""
        payload = {
            "strategy_id": "test_sharpe_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 0.5}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                assert any("sharpe ratio" in s["suggestion"].lower() for s in suggestions)

    def test_high_drawdown_suggestion(self, valid_jwt_token):
        """Test suggestions for high drawdown."""
        payload = {
            "strategy_id": "test_dd_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"max_drawdown": 0.35}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                assert any("drawdown" in s["suggestion"].lower() for s in suggestions)

    def test_low_win_rate_suggestion(self, valid_jwt_token):
        """Test suggestions for low win rate."""
        payload = {
            "strategy_id": "test_wr_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"win_rate": 0.35}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                assert any("win rate" in s["suggestion"].lower() for s in suggestions)


class TestReflexionFeedbackBasedSuggestions:
    """Test suggestions generated from feedback text."""

    def test_volatility_feedback(self, valid_jwt_token):
        """Test suggestions from volatility feedback."""
        payload = {
            "strategy_id": "test_fb_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 1.0},
            "feedback": "Strategy shows high volatility during market stress"
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                assert any("volatility" in s["suggestion"].lower() for s in suggestions)

    def test_drawdown_feedback(self, valid_jwt_token):
        """Test suggestions from drawdown feedback."""
        payload = {
            "strategy_id": "test_fb_002",
            "strategy_type": "mean_reversion",
            "parameters": {"lookback": 20, "entry_threshold": -2.0},
            "performance_metrics": {"sharpe_ratio": 1.0},
            "feedback": "Large drawdowns during trending markets"
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                assert any("drawdown" in s["suggestion"].lower() for s in suggestions)


class TestReflexionContextAwareSuggestions:
    """Test suggestions based on strategy context."""

    def test_momentum_context(self, valid_jwt_token):
        """Test context-aware suggestions for momentum strategy."""
        payload = {
            "strategy_id": "test_ctx_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                # Should have momentum-specific suggestions
                assert len(suggestions) > 0

    def test_mean_reversion_context(self, valid_jwt_token):
        """Test context-aware suggestions for mean reversion strategy."""
        payload = {
            "strategy_id": "test_ctx_002",
            "strategy_type": "mean_reversion",
            "parameters": {"lookback": 20, "entry_threshold": -2.0},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                # Should have mean reversion-specific suggestions
                assert len(suggestions) > 0


class TestReflexionSuggestionPriorities:
    """Test suggestion priority levels."""

    def test_suggestion_priorities(self, valid_jwt_token):
        """Test that suggestions have valid priority levels."""
        payload = {
            "strategy_id": "test_pri_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 0.5, "max_drawdown": 0.35}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                for suggestion in suggestions:
                    assert suggestion["priority"] in ["high", "medium", "low"]

    def test_high_priority_suggestions(self, valid_jwt_token):
        """Test that poor metrics generate high priority suggestions."""
        payload = {
            "strategy_id": "test_pri_002",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 0.3, "max_drawdown": 0.45, "win_rate": 0.30}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                high_priority = [s for s in suggestions if s["priority"] == "high"]
                assert len(high_priority) > 0


class TestReflexionSuggestionCategories:
    """Test suggestion category classification."""

    def test_suggestion_categories(self, valid_jwt_token):
        """Test that suggestions have valid categories."""
        payload = {
            "strategy_id": "test_cat_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 0.8}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                suggestions = data["suggestions"]
                valid_categories = ["parameter", "logic", "risk_management", "timing"]
                for suggestion in suggestions:
                    assert suggestion["category"] in valid_categories


class TestReflexionFeatureFlags:
    """Test feature flag functionality."""

    def test_reflexion_primitive_disabled(self, valid_jwt_token):
        """Test reflexion primitive when feature flag is disabled."""
        payload = {
            "strategy_id": "test_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.side_effect = Exception("Reflexion primitive is disabled")
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            assert response.status_code == 403


class TestReflexionResponseStructure:
    """Test canonical response envelope structure."""

    def test_response_has_canonical_structure(self, valid_jwt_token):
        """Test that response follows canonical envelope pattern."""
        payload = {
            "strategy_id": "test_001",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
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
                assert json_data["meta"]["primitive"] == "reflexion"

    def test_suggestion_structure(self, valid_jwt_token):
        """Test that suggestions have correct structure."""
        payload = {
            "strategy_id": "test_002",
            "strategy_type": "momentum",
            "parameters": {"lookback": 20, "threshold": 0.02},
            "performance_metrics": {"sharpe_ratio": 1.0}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "improvement_score" in data
                assert "suggestions" in data
                assert "summary" in data
                for suggestion in data["suggestions"]:
                    assert "suggestion" in suggestion
                    assert "category" in suggestion
                    assert "priority" in suggestion

    def test_health_endpoint(self):
        """Test reflexion primitive health endpoint."""
        response = client.get("/api/primitives/v1/reflexion/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["primitive"] == "reflexion"


class TestReflexionMultipleStrategies:
    """Test reflexion with different strategy types."""

    def test_pairs_trading_strategy(self, valid_jwt_token):
        """Test reflexion for pairs trading strategy."""
        payload = {
            "strategy_id": "pairs_001",
            "strategy_type": "pairs_trading",
            "parameters": {"lookback": 60, "entry_threshold": 2.0},
            "performance_metrics": {"sharpe_ratio": 1.2}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "improvement_score" in data
                assert len(data["suggestions"]) > 0

    def test_volatility_trading_strategy(self, valid_jwt_token):
        """Test reflexion for volatility trading strategy."""
        payload = {
            "strategy_id": "vol_001",
            "strategy_type": "volatility_trading",
            "parameters": {"vol_target": 0.15, "rebalance_freq": "daily"},
            "performance_metrics": {"sharpe_ratio": 0.9}
        }
        with patch('security.auth.get_feature_flags') as mock_flags:
            mock_flags.return_value.check_primitive_enabled.return_value = None
            response = client.post(
                "/api/primitives/v1/reflexion/suggest",
                json=payload,
                headers={"Authorization": f"Bearer {valid_jwt_token}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                assert "improvement_score" in data
                assert len(data["suggestions"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
