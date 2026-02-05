"""
Integration tests for advanced features
Portfolio optimization, risk analytics, ML optimization, risk management
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient
from api.main import app
from api.advanced.portfolio_optimizer import PortfolioOptimizer, OptimizationMethod
from api.advanced.risk_metrics import RiskAnalyzer
from api.advanced.ml_optimizer import StrategyOptimizer
from api.advanced.risk_management import RiskManager, PositionSizeMethod

client = TestClient(app)


# Mock authentication
@pytest.fixture
def auth_headers():
    """Get authentication headers for testing"""
    # Register and login
    client.post("/api/auth/register", json={
        "username": "testuser_advanced",
        "email": "advanced@test.com",
        "password": "Test123!@#"
    })
    
    response = client.post("/api/auth/login", data={
        "username": "testuser_advanced",
        "password": "Test123!@#"
    })
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestPortfolioOptimization:
    """Test portfolio optimization endpoints"""
    
    def test_optimize_max_sharpe(self, auth_headers):
        """Test maximum Sharpe ratio optimization"""
        # Generate sample returns (3 assets, 252 days)
        np.random.seed(42)
        returns = np.random.randn(3, 252) * 0.01
        
        response = client.post(
            "/api/advanced/portfolio/optimize",
            json={
                "returns": returns.tolist(),
                "method": "max_sharpe",
                "risk_free_rate": 0.02
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "weights" in data
        assert len(data["weights"]) == 3
        assert abs(sum(data["weights"]) - 1.0) < 0.01  # Weights sum to ~1
        assert "sharpe_ratio" in data
        assert "expected_return" in data
        assert "volatility" in data
    
    def test_optimize_min_variance(self, auth_headers):
        """Test minimum variance optimization"""
        np.random.seed(42)
        returns = np.random.randn(3, 252) * 0.01
        
        response = client.post(
            "/api/advanced/portfolio/optimize",
            json={
                "returns": returns.tolist(),
                "method": "min_variance"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "volatility" in data
    
    def test_efficient_frontier(self, auth_headers):
        """Test efficient frontier calculation"""
        np.random.seed(42)
        returns = np.random.randn(3, 252) * 0.01
        
        response = client.post(
            "/api/advanced/portfolio/efficient-frontier?n_points=20",
            json={
                "returns": returns.tolist()
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["n_points"] == 20
        assert len(data["frontier"]) == 20
        
        # Check that frontier is sorted by volatility
        vols = [p["volatility"] for p in data["frontier"]]
        assert vols == sorted(vols)


class TestRiskAnalytics:
    """Test risk analytics endpoints"""
    
    def test_risk_analysis_complete(self, auth_headers):
        """Test comprehensive risk analysis"""
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01
        equity_curve = np.cumprod(1 + returns)
        
        response = client.post(
            "/api/advanced/risk/analyze",
            json={
                "returns": returns.tolist(),
                "equity_curve": equity_curve.tolist(),
                "risk_free_rate": 0.02
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "metrics" in data
        
        metrics = data["metrics"]
        assert "volatility" in metrics
        assert "risk_adjusted_returns" in metrics
        assert "drawdown" in metrics
        assert "value_at_risk" in metrics
        assert "distribution" in metrics
        
        # Check specific metrics
        assert "sharpe_ratio" in metrics["risk_adjusted_returns"]
        assert "sortino_ratio" in metrics["risk_adjusted_returns"]
        assert "calmar_ratio" in metrics["risk_adjusted_returns"]
        assert "max_drawdown" in metrics["drawdown"]
        assert "var_95" in metrics["value_at_risk"]
        assert "cvar_95" in metrics["value_at_risk"]


class TestMLOptimization:
    """Test ML-based strategy optimization"""
    
    def test_strategy_optimization(self, auth_headers):
        """Test strategy parameter optimization"""
        response = client.post(
            "/api/advanced/strategy/optimize",
            json={
                "strategy_id": "moving_average_crossover",
                "param_space": {
                    "fast_period": {"type": "int", "low": 5, "high": 20, "step": 5},
                    "slow_period": {"type": "int", "low": 20, "high": 50, "step": 10}
                },
                "data_start": "2022-01-01",
                "data_end": "2023-01-01",
                "n_trials": 10,
                "objective_metric": "sharpe_ratio"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "best_params" in data
        assert "best_value" in data
        assert "n_trials" in data
        assert data["n_trials"] == 10
        assert "optimization_time" in data
        assert "history" in data


class TestRiskManagement:
    """Test risk management endpoints"""
    
    def test_position_sizing_volatility(self, auth_headers):
        """Test volatility-based position sizing"""
        response = client.post(
            "/api/advanced/risk/position-size?initial_capital=100000",
            json={
                "symbol": "AAPL",
                "signal_strength": 0.8,
                "current_price": 150.0,
                "volatility": 0.25,
                "method": "volatility"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "position_size" in data
        assert "position_value" in data
        assert "position_pct" in data
        assert data["position_size"] > 0
        assert data["position_pct"] <= 0.25  # Max 25% per position
    
    def test_position_sizing_kelly(self, auth_headers):
        """Test Kelly criterion position sizing"""
        response = client.post(
            "/api/advanced/risk/position-size?initial_capital=100000",
            json={
                "symbol": "AAPL",
                "signal_strength": 0.6,
                "current_price": 150.0,
                "volatility": 0.20,
                "method": "kelly"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["position_size"] > 0
    
    def test_stop_loss_calculation(self, auth_headers):
        """Test stop-loss and take-profit calculation"""
        response = client.post(
            "/api/advanced/risk/stop-loss?risk_reward_ratio=2.5",
            json={
                "entry_price": 150.0,
                "volatility": 0.25,
                "atr": 3.5,
                "method": "atr"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stop_loss" in data
        assert "take_profit" in data
        assert "risk_amount" in data
        assert "reward_amount" in data
        assert "risk_reward_ratio" in data
        
        # Stop loss should be below entry
        assert data["stop_loss"] < data["entry_price"]
        # Take profit should be above entry
        assert data["take_profit"] > data["entry_price"]
        # Risk/reward ratio should be close to requested
        assert abs(data["risk_reward_ratio"] - 2.5) < 0.5
    
    def test_risk_limits(self, auth_headers):
        """Test risk limits endpoint"""
        response = client.get(
            "/api/advanced/risk/limits",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "limits" in data
        
        limits = data["limits"]
        assert "max_position_size" in limits
        assert "max_portfolio_leverage" in limits
        assert "max_daily_loss" in limits
        assert "max_drawdown" in limits


class TestPortfolioOptimizerUnit:
    """Unit tests for portfolio optimizer"""
    
    def test_max_sharpe_optimization(self):
        """Test maximum Sharpe ratio optimization"""
        np.random.seed(42)
        returns = np.random.randn(3, 252) * 0.01
        
        optimizer = PortfolioOptimizer(risk_free_rate=0.02)
        result = optimizer.optimize(returns, OptimizationMethod.MAX_SHARPE, {})
        
        assert result.expected_return is not None
        assert result.volatility > 0
        assert len(result.weights) == 3
        assert abs(sum(result.weights) - 1.0) < 0.01
        assert all(w >= 0 for w in result.weights)
    
    def test_risk_parity(self):
        """Test risk parity optimization"""
        np.random.seed(42)
        returns = np.random.randn(3, 252) * 0.01
        
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize(returns, OptimizationMethod.RISK_PARITY, {})
        
        assert len(result.weights) == 3
        assert all(w > 0 for w in result.weights)  # All weights positive in risk parity


class TestRiskAnalyzerUnit:
    """Unit tests for risk analyzer"""
    
    def test_calculate_all_metrics(self):
        """Test comprehensive risk metrics calculation"""
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01
        equity_curve = np.cumprod(1 + returns)
        
        analyzer = RiskAnalyzer(risk_free_rate=0.02)
        metrics = analyzer.calculate_all_metrics(returns, equity_curve)
        
        assert metrics.volatility > 0
        assert metrics.sharpe_ratio is not None
        assert metrics.sortino_ratio is not None
        assert metrics.max_drawdown <= 0
        assert metrics.var_95 <= 0
        assert metrics.cvar_95 <= 0
        assert metrics.cvar_95 <= metrics.var_95  # CVaR should be worse than VaR
    
    def test_var_cvar(self):
        """Test VaR and CVaR calculations"""
        np.random.seed(42)
        returns = np.random.randn(1000) * 0.01
        
        analyzer = RiskAnalyzer()
        var_95 = analyzer.calculate_var(returns, 0.95)
        cvar_95 = analyzer.calculate_cvar(returns, 0.95)
        
        assert var_95 < 0  # VaR should be negative (loss)
        assert cvar_95 < var_95  # CVaR should be worse than VaR


class TestRiskManagerUnit:
    """Unit tests for risk manager"""
    
    def test_position_sizing(self):
        """Test different position sizing methods"""
        manager = RiskManager(100000)
        
        # Test volatility sizing
        size_vol = manager.calculate_position_size(
            "AAPL", 0.8, 150.0, 0.25, PositionSizeMethod.VOLATILITY
        )
        assert size_vol > 0
        assert size_vol * 150.0 <= 100000 * 0.25  # Within position limit
        
        # Test fixed sizing
        size_fixed = manager.calculate_position_size(
            "AAPL", 0.8, 150.0, 0.25, PositionSizeMethod.FIXED
        )
        assert size_fixed > 0
    
    def test_risk_limits(self):
        """Test risk limit checking"""
        manager = RiskManager(100000)
        
        # Add position
        manager.add_position("AAPL", 100, 150.0)
        
        # Check limits
        checks = manager.check_risk_limits()
        assert checks["within_position_limit"] is True
        assert checks["within_leverage_limit"] is True
    
    def test_position_lifecycle(self):
        """Test complete position lifecycle"""
        manager = RiskManager(100000)
        
        # Add position
        manager.add_position("AAPL", 100, 150.0, stop_loss=145.0, take_profit=160.0)
        assert "AAPL" in manager.positions
        
        # Update position
        manager.update_position("AAPL", 155.0)
        assert manager.positions["AAPL"].current_price == 155.0
        
        # Close position
        result = manager.close_position("AAPL", 155.0)
        assert result["pnl"] == 500.0  # (155-150) * 100
        assert "AAPL" not in manager.positions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
