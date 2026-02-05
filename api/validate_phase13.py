#!/usr/bin/env python3
"""
Quick validation script for Phase 13 advanced features
Tests basic functionality without full integration tests
"""
import sys
import numpy as np
from pathlib import Path

# Add api to path
sys.path.insert(0, str(Path(__file__).parent))

def test_portfolio_optimizer():
    """Test portfolio optimizer"""
    print("Testing Portfolio Optimizer...")
    from advanced.portfolio_optimizer import PortfolioOptimizer, OptimizationMethod
    
    np.random.seed(42)
    returns = np.random.randn(3, 252) * 0.01
    
    optimizer = PortfolioOptimizer(risk_free_rate=0.02)
    result = optimizer.optimize(returns, OptimizationMethod.MAX_SHARPE, {})
    
    assert result.expected_return is not None
    assert result.volatility > 0
    assert len(result.weights) == 3
    assert abs(sum(result.weights) - 1.0) < 0.01
    print("✅ Portfolio Optimizer works!")
    return True

def test_risk_analyzer():
    """Test risk analyzer"""
    print("Testing Risk Analyzer...")
    from advanced.risk_metrics import RiskAnalyzer
    
    np.random.seed(42)
    returns = np.random.randn(252) * 0.01
    equity_curve = np.cumprod(1 + returns)
    
    analyzer = RiskAnalyzer(risk_free_rate=0.02)
    metrics = analyzer.calculate_all_metrics(returns, equity_curve)
    
    assert metrics.volatility > 0
    assert metrics.sharpe_ratio is not None
    assert metrics.max_drawdown <= 0
    assert metrics.var_95 <= 0
    print("✅ Risk Analyzer works!")
    return True

def test_risk_manager():
    """Test risk manager"""
    print("Testing Risk Manager...")
    from advanced.risk_management import RiskManager, PositionSizeMethod
    
    manager = RiskManager(100000)
    
    # Test position sizing
    size = manager.calculate_position_size(
        "AAPL", 0.8, 150.0, 0.25, PositionSizeMethod.VOLATILITY
    )
    assert size > 0
    
    # Test position lifecycle
    manager.add_position("AAPL", 100, 150.0)
    assert "AAPL" in manager.positions
    
    result = manager.close_position("AAPL", 155.0)
    assert result["pnl"] == 500.0
    assert "AAPL" not in manager.positions
    
    print("✅ Risk Manager works!")
    return True

def test_ml_optimizer():
    """Test ML optimizer"""
    print("Testing ML Optimizer...")
    from advanced.ml_optimizer import StrategyOptimizer
    
    # Create optimizer with minimal trials
    optimizer = StrategyOptimizer(n_trials=5)
    
    # Mock backtest function
    def backtest(params, data):
        return {"sharpe_ratio": np.random.uniform(0.5, 2.0)}
    
    # Simple parameter space
    param_space = {
        "period": {"type": "int", "low": 5, "high": 20, "step": 5}
    }
    
    result = optimizer.optimize(backtest, param_space, np.random.randn(100))
    
    assert result.best_params is not None
    assert result.n_trials == 5
    print("✅ ML Optimizer works!")
    return True

def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("Phase 13 Advanced Features Validation")
    print("="*60 + "\n")
    
    tests = [
        test_portfolio_optimizer,
        test_risk_analyzer,
        test_risk_manager,
        test_ml_optimizer
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print()
            results.append(False)
    
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All Phase 13 features validated successfully!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
