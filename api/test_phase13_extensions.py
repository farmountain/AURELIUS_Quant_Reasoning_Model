"""
Integration tests for Phase 13 extensions
Custom indicators and multi-asset support
"""
import pytest
import numpy as np
from api.advanced.indicators import (
    calculate_indicator,
    calculate_multiple_indicators,
    indicator_registry,
    MovingAverage,
    RSI,
    MACD,
    BollingerBands,
    ATR
)
from api.advanced.multi_asset import (
    AssetClass,
    AssetMetadata,
    OptionPricer,
    CrossAssetAnalyzer,
    MultiAssetPortfolio,
    AssetRiskModel
)
from datetime import datetime


class TestCustomIndicators:
    """Test custom indicators framework"""
    
    def test_sma_calculation(self):
        """Test Simple Moving Average"""
        data = {'close': np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])}
        
        result = calculate_indicator('sma', data, period=5)
        
        assert 'sma' in result
        assert len(result['sma']) == len(data['close'])
        # First 4 values should be NaN
        assert np.isnan(result['sma'][:4]).all()
        # 5th value should be average of first 5
        assert abs(result['sma'][4] - 102.2) < 0.1
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average"""
        data = {'close': np.array([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])}
        
        result = calculate_indicator('ema', data, period=5)
        
        assert 'ema' in result
        assert len(result['ema']) == len(data['close'])
        assert result['ema'][0] == 100  # First value equals first close
    
    def test_rsi_calculation(self):
        """Test RSI indicator"""
        # Create trending data
        close = np.array([100, 102, 104, 103, 105, 107, 106, 108, 110, 109, 111, 113, 112, 114, 116])
        data = {'close': close}
        
        result = calculate_indicator('rsi', data, period=14)
        
        assert 'rsi' in result
        assert len(result['rsi']) == len(close)
        # RSI should be between 0 and 100
        valid_rsi = result['rsi'][~np.isnan(result['rsi'])]
        assert np.all(valid_rsi >= 0)
        assert np.all(valid_rsi <= 100)
    
    def test_macd_calculation(self):
        """Test MACD indicator"""
        close = np.linspace(100, 120, 50)  # Trending upward
        data = {'close': close}
        
        result = calculate_indicator('macd', data)
        
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result
        assert len(result['macd']) == len(close)
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands"""
        close = np.random.randn(50) * 5 + 100
        data = {'close': close}
        
        result = calculate_indicator('bbands', data, period=20, std_dev=2)
        
        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result
        # Upper should be above middle, middle above lower
        valid_idx = 20  # After warmup
        assert result['upper'][valid_idx] > result['middle'][valid_idx]
        assert result['middle'][valid_idx] > result['lower'][valid_idx]
    
    def test_atr_calculation(self):
        """Test Average True Range"""
        np.random.seed(42)
        n = 50
        close = np.cumsum(np.random.randn(n) * 2) + 100
        high = close + np.abs(np.random.randn(n))
        low = close - np.abs(np.random.randn(n))
        
        data = {'high': high, 'low': low, 'close': close}
        
        result = calculate_indicator('atr', data, period=14)
        
        assert 'atr' in result
        assert len(result['atr']) == len(close)
        # ATR should be positive
        valid_atr = result['atr'][~np.isnan(result['atr'])]
        assert np.all(valid_atr > 0)
    
    def test_multiple_indicators(self):
        """Test calculating multiple indicators at once"""
        close = np.random.randn(50) * 5 + 100
        data = {'close': close}
        
        indicators = [
            {"name": "sma", "params": {"period": 20}},
            {"name": "ema", "params": {"period": 20}},
            {"name": "rsi", "params": {"period": 14}}
        ]
        
        results = calculate_multiple_indicators(indicators, data)
        
        assert 'sma' in results
        assert 'ema' in results
        assert 'rsi' in results
    
    def test_indicator_registry(self):
        """Test indicator registry"""
        indicators = indicator_registry.list_indicators()
        
        assert len(indicators) >= 6
        indicator_names = [ind['key'] for ind in indicators]
        assert 'sma' in indicator_names
        assert 'ema' in indicator_names
        assert 'rsi' in indicator_names
        assert 'macd' in indicator_names
        assert 'bbands' in indicator_names
        assert 'atr' in indicator_names


class TestMultiAsset:
    """Test multi-asset support"""
    
    def test_asset_metadata(self):
        """Test asset metadata creation"""
        asset = AssetMetadata(
            symbol="AAPL",
            asset_class=AssetClass.STOCK,
            exchange="NASDAQ",
            currency="USD",
            tick_size=0.01
        )
        
        assert asset.symbol == "AAPL"
        assert asset.asset_class == AssetClass.STOCK
        assert asset.contract_size == 1.0
    
    def test_option_pricing_call(self):
        """Test Black-Scholes call option pricing"""
        asset = AssetMetadata("TEST", AssetClass.OPTION, "TEST", "USD")
        pricer = OptionPricer(asset)
        
        result = pricer.black_scholes(
            spot=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            volatility=0.20,
            risk_free_rate=0.05,
            option_type='call'
        )
        
        assert 'price' in result
        assert 'delta' in result
        assert 'gamma' in result
        assert 'theta' in result
        assert 'vega' in result
        assert 'rho' in result
        
        # ATM call delta should be around 0.5-0.6 (higher due to positive interest rate)
        assert 0.45 < result['delta'] < 0.60
        
        # Gamma should be positive
        assert result['gamma'] > 0
        
        # Theta should be negative (time decay)
        assert result['theta'] < 0
        
        # Vega should be positive
        assert result['vega'] > 0
    
    def test_option_pricing_put(self):
        """Test Black-Scholes put option pricing"""
        asset = AssetMetadata("TEST", AssetClass.OPTION, "TEST", "USD")
        pricer = OptionPricer(asset)
        
        result = pricer.black_scholes(
            spot=100.0,
            strike=100.0,
            time_to_expiry=0.25,
            volatility=0.20,
            risk_free_rate=0.05,
            option_type='put'
        )
        
        # ATM put delta should be around -0.4 to -0.5 (less negative due to positive interest rate)
        assert -0.55 < result['delta'] < -0.40
        
        # Put should have positive gamma
        assert result['gamma'] > 0
    
    def test_correlation_matrix(self):
        """Test correlation matrix calculation"""
        np.random.seed(42)
        
        returns = {
            'AAPL': np.random.randn(252) * 0.02,
            'MSFT': np.random.randn(252) * 0.018,
            'GOOGL': np.random.randn(252) * 0.019
        }
        
        analyzer = CrossAssetAnalyzer([])
        corr_matrix = analyzer.calculate_correlation_matrix(returns)
        
        assert corr_matrix.shape == (3, 3)
        # Diagonal should be 1
        assert np.allclose(np.diag(corr_matrix), 1.0)
        # Should be symmetric
        assert np.allclose(corr_matrix, corr_matrix.T)
        # Values should be between -1 and 1
        assert np.all(corr_matrix >= -1)
        assert np.all(corr_matrix <= 1)
    
    def test_beta_calculation(self):
        """Test beta calculation"""
        np.random.seed(42)
        
        market_returns = np.random.randn(252) * 0.01
        asset_returns = 1.2 * market_returns + np.random.randn(252) * 0.005
        
        analyzer = CrossAssetAnalyzer([])
        beta = analyzer.calculate_beta_to_market(asset_returns, market_returns)
        
        # Beta should be close to 1.2
        assert 1.0 < beta < 1.4
    
    def test_multi_asset_portfolio(self):
        """Test multi-asset portfolio management"""
        assets = [
            AssetMetadata("AAPL", AssetClass.STOCK, "NASDAQ", "USD"),
            AssetMetadata("ESZ23", AssetClass.FUTURE, "CME", "USD", contract_size=50),
            AssetMetadata("BTC-USD", AssetClass.CRYPTO, "COINBASE", "USD")
        ]
        
        portfolio = MultiAssetPortfolio(assets)
        
        # Add positions
        portfolio.add_position("AAPL", 100, 150.0, datetime.now())
        portfolio.add_position("ESZ23", 5, 4500.0, datetime.now())
        portfolio.add_position("BTC-USD", 0.5, 45000.0, datetime.now())
        
        assert len(portfolio.positions) == 3
        
        # Calculate value
        current_prices = {"AAPL": 155.0, "ESZ23": 4550.0, "BTC-USD": 46000.0}
        total_value = portfolio.calculate_portfolio_value(current_prices)
        
        # Expected: 100*155 + 5*4550*50 + 0.5*46000
        expected = 15500 + 1137500 + 23000
        assert abs(total_value - expected) < 1.0
        
        # Calculate P&L
        pnl = portfolio.calculate_portfolio_pnl(current_prices)
        
        assert 'total_pnl' in pnl
        assert 'pnl_by_asset' in pnl
        assert 'pnl_by_class' in pnl
        
        # Expected P&L: (155-150)*100 + (4550-4500)*5*50 + (46000-45000)*0.5
        expected_pnl = 500 + 12500 + 500
        assert abs(pnl['total_pnl'] - expected_pnl) < 1.0
    
    def test_exposure_by_class(self):
        """Test exposure breakdown by asset class"""
        assets = [
            AssetMetadata("AAPL", AssetClass.STOCK, "NASDAQ", "USD"),
            AssetMetadata("MSFT", AssetClass.STOCK, "NASDAQ", "USD"),
            AssetMetadata("BTC", AssetClass.CRYPTO, "COINBASE", "USD")
        ]
        
        portfolio = MultiAssetPortfolio(assets)
        portfolio.add_position("AAPL", 100, 150.0, datetime.now())
        portfolio.add_position("MSFT", 50, 300.0, datetime.now())
        portfolio.add_position("BTC", 1, 45000.0, datetime.now())
        
        current_prices = {"AAPL": 150.0, "MSFT": 300.0, "BTC": 45000.0}
        exposure = portfolio.get_exposure_by_class(current_prices)
        
        assert 'stock' in exposure
        assert 'crypto' in exposure
        # Stock exposure: 100*150 + 50*300 = 30000
        assert abs(exposure['stock'] - 30000) < 1.0
        # Crypto exposure: 1*45000 = 45000
        assert abs(exposure['crypto'] - 45000) < 1.0
    
    def test_var_by_asset_class(self):
        """Test VaR calculation with asset class multipliers"""
        np.random.seed(42)
        returns = np.random.randn(1000) * 0.01
        
        stock_var = AssetRiskModel.calculate_var_by_asset_class(
            AssetClass.STOCK, returns, 0.95
        )
        
        crypto_var = AssetRiskModel.calculate_var_by_asset_class(
            AssetClass.CRYPTO, returns, 0.95
        )
        
        # Crypto VaR should be more conservative (larger negative)
        assert crypto_var < stock_var
    
    def test_margin_requirements(self):
        """Test margin requirement calculation"""
        # Stock margin (50% base)
        stock_margin = AssetRiskModel.calculate_margin_requirement(
            AssetClass.STOCK, 10000.0, 0.20
        )
        assert stock_margin > 0
        assert stock_margin < 10000  # Should be less than position value
        
        # Crypto margin (75% base)
        crypto_margin = AssetRiskModel.calculate_margin_requirement(
            AssetClass.CRYPTO, 10000.0, 0.50
        )
        # Crypto should require more margin than stocks
        assert crypto_margin > stock_margin


class TestAPIEndpoints:
    """Test API endpoints for indicators and multi-asset"""
    
    # These tests would require the FastAPI test client
    # For now, just verify imports work
    
    def test_imports(self):
        """Test that all modules can be imported"""
        from api.advanced.indicators import indicator_registry
        from api.advanced.multi_asset import AssetClass
        from api.routers.advanced import router
        
        assert indicator_registry is not None
        assert AssetClass.STOCK is not None
        assert router is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
