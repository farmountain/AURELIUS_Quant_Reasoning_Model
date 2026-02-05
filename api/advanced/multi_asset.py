"""
Multi-Asset Support Framework
Support for stocks, futures, options, crypto with asset-specific models
"""
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AssetClass(Enum):
    """Supported asset classes"""
    STOCK = "stock"
    FUTURE = "future"
    OPTION = "option"
    CRYPTO = "crypto"
    FX = "fx"
    COMMODITY = "commodity"


@dataclass
class AssetMetadata:
    """Metadata for an asset"""
    symbol: str
    asset_class: AssetClass
    exchange: str
    currency: str
    contract_size: float = 1.0
    tick_size: float = 0.01
    trading_hours: Optional[Dict[str, Any]] = None


class AssetPricer:
    """Base class for asset pricing"""
    
    def __init__(self, asset: AssetMetadata):
        self.asset = asset
    
    def calculate_value(self, position_size: float, price: float) -> float:
        """Calculate position value"""
        return position_size * price * self.asset.contract_size
    
    def calculate_pnl(
        self,
        position_size: float,
        entry_price: float,
        current_price: float
    ) -> float:
        """Calculate profit/loss"""
        return position_size * (current_price - entry_price) * self.asset.contract_size


class StockPricer(AssetPricer):
    """Pricer for stocks"""
    
    def __init__(self, asset: AssetMetadata):
        super().__init__(asset)
    
    def calculate_dividend_yield(self, price: float, annual_dividend: float) -> float:
        """Calculate dividend yield"""
        return annual_dividend / price


class FuturePricer(AssetPricer):
    """Pricer for futures"""
    
    def __init__(self, asset: AssetMetadata):
        super().__init__(asset)
    
    def calculate_basis(self, futures_price: float, spot_price: float) -> float:
        """Calculate basis (futures - spot)"""
        return futures_price - spot_price
    
    def calculate_fair_value(
        self,
        spot_price: float,
        risk_free_rate: float,
        time_to_expiry: float,
        carry_cost: float = 0.0
    ) -> float:
        """Calculate fair value of futures"""
        return spot_price * np.exp((risk_free_rate + carry_cost) * time_to_expiry)


class OptionPricer(AssetPricer):
    """Pricer for options using Black-Scholes"""
    
    def __init__(self, asset: AssetMetadata):
        super().__init__(asset)
    
    def black_scholes(
        self,
        spot: float,
        strike: float,
        time_to_expiry: float,
        volatility: float,
        risk_free_rate: float,
        option_type: str = "call"
    ) -> Dict[str, float]:
        """
        Calculate option price and Greeks using Black-Scholes
        
        Returns:
            Dictionary with price, delta, gamma, theta, vega, rho
        """
        from scipy.stats import norm
        
        # Calculate d1 and d2
        d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        if option_type.lower() == "call":
            # Call option
            price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
            delta = norm.cdf(d1)
            theta = (-spot * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry)) 
                    - risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
            rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
        else:
            # Put option
            price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)
            delta = -norm.cdf(-d1)
            theta = (-spot * norm.pdf(d1) * volatility / (2 * np.sqrt(time_to_expiry)) 
                    + risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2))
            rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2)
        
        # Greeks common to both call and put
        gamma = norm.pdf(d1) / (spot * volatility * np.sqrt(time_to_expiry))
        vega = spot * norm.pdf(d1) * np.sqrt(time_to_expiry)
        
        return {
            "price": price,
            "delta": delta,
            "gamma": gamma,
            "theta": theta / 365,  # Per day
            "vega": vega / 100,    # Per 1% volatility
            "rho": rho / 100       # Per 1% rate change
        }


class CryptoPricer(AssetPricer):
    """Pricer for cryptocurrencies"""
    
    def __init__(self, asset: AssetMetadata):
        super().__init__(asset)
    
    def calculate_funding_rate(
        self,
        perpetual_price: float,
        index_price: float,
        funding_interval_hours: float = 8.0
    ) -> float:
        """Calculate funding rate for perpetual swaps"""
        return ((perpetual_price - index_price) / index_price) * (24 / funding_interval_hours)


class CrossAssetAnalyzer:
    """Analyze relationships across multiple assets"""
    
    def __init__(self, assets: List[AssetMetadata]):
        self.assets = assets
    
    def calculate_correlation_matrix(
        self,
        returns: Dict[str, np.ndarray]
    ) -> np.ndarray:
        """Calculate correlation matrix across assets"""
        symbols = list(returns.keys())
        n = len(symbols)
        
        corr_matrix = np.zeros((n, n))
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    corr = np.corrcoef(returns[symbol1], returns[symbol2])[0, 1]
                    corr_matrix[i, j] = corr
        
        return corr_matrix
    
    def calculate_beta_to_market(
        self,
        asset_returns: np.ndarray,
        market_returns: np.ndarray
    ) -> float:
        """Calculate asset beta relative to market"""
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 0.0
        
        return covariance / market_variance
    
    def identify_cointegrated_pairs(
        self,
        price_series: Dict[str, np.ndarray],
        significance_level: float = 0.05
    ) -> List[tuple]:
        """
        Identify cointegrated asset pairs using Engle-Granger test
        
        Returns:
            List of (symbol1, symbol2, p_value) tuples
        """
        from statsmodels.tsa.stattools import coint
        
        symbols = list(price_series.keys())
        cointegrated_pairs = []
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols[i+1:], i+1):
                try:
                    _, p_value, _ = coint(price_series[symbol1], price_series[symbol2])
                    
                    if p_value < significance_level:
                        cointegrated_pairs.append((symbol1, symbol2, p_value))
                except Exception as e:
                    logger.warning(f"Cointegration test failed for {symbol1}-{symbol2}: {e}")
        
        return sorted(cointegrated_pairs, key=lambda x: x[2])


class AssetRiskModel:
    """Risk model for different asset classes"""
    
    @staticmethod
    def calculate_var_by_asset_class(
        asset_class: AssetClass,
        returns: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """Calculate VaR with asset-class specific adjustments"""
        base_var = np.percentile(returns, (1 - confidence) * 100)
        
        # Asset-class specific risk multipliers
        multipliers = {
            AssetClass.STOCK: 1.0,
            AssetClass.FUTURE: 1.5,
            AssetClass.OPTION: 2.0,
            AssetClass.CRYPTO: 2.5,
            AssetClass.FX: 1.2,
            AssetClass.COMMODITY: 1.3
        }
        
        multiplier = multipliers.get(asset_class, 1.0)
        return base_var * multiplier
    
    @staticmethod
    def calculate_margin_requirement(
        asset_class: AssetClass,
        position_value: float,
        volatility: float
    ) -> float:
        """Calculate margin requirement based on asset class"""
        # Base margin rates
        base_rates = {
            AssetClass.STOCK: 0.50,      # 50% for stocks
            AssetClass.FUTURE: 0.10,     # 10% for futures
            AssetClass.OPTION: 1.00,     # 100% for options (cash secured)
            AssetClass.CRYPTO: 0.75,     # 75% for crypto
            AssetClass.FX: 0.02,         # 2% for FX
            AssetClass.COMMODITY: 0.15   # 15% for commodities
        }
        
        base_rate = base_rates.get(asset_class, 0.50)
        
        # Adjust for volatility
        vol_adjustment = 1.0 + (volatility - 0.20) * 2.0  # Adjust around 20% vol baseline
        vol_adjustment = max(0.5, min(vol_adjustment, 3.0))  # Cap between 0.5x and 3.0x
        
        return position_value * base_rate * vol_adjustment


class MultiAssetPortfolio:
    """Portfolio management across multiple asset classes"""
    
    def __init__(self, assets: List[AssetMetadata]):
        self.assets = {asset.symbol: asset for asset in assets}
        self.positions: Dict[str, Dict[str, Any]] = {}
    
    def add_position(
        self,
        symbol: str,
        size: float,
        entry_price: float,
        entry_time: datetime
    ):
        """Add a position"""
        if symbol not in self.assets:
            raise ValueError(f"Unknown asset: {symbol}")
        
        self.positions[symbol] = {
            "size": size,
            "entry_price": entry_price,
            "entry_time": entry_time,
            "asset": self.assets[symbol]
        }
    
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        total_value = 0.0
        
        for symbol, position in self.positions.items():
            asset = position["asset"]
            pricer = self._get_pricer(asset)
            
            current_price = current_prices.get(symbol, position["entry_price"])
            value = pricer.calculate_value(position["size"], current_price)
            total_value += value
        
        return total_value
    
    def calculate_portfolio_pnl(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """Calculate portfolio P&L breakdown"""
        total_pnl = 0.0
        pnl_by_asset = {}
        pnl_by_class = {}
        
        for symbol, position in self.positions.items():
            asset = position["asset"]
            pricer = self._get_pricer(asset)
            
            current_price = current_prices.get(symbol, position["entry_price"])
            pnl = pricer.calculate_pnl(
                position["size"],
                position["entry_price"],
                current_price
            )
            
            pnl_by_asset[symbol] = pnl
            total_pnl += pnl
            
            # Aggregate by asset class
            asset_class = asset.asset_class.value
            pnl_by_class[asset_class] = pnl_by_class.get(asset_class, 0.0) + pnl
        
        return {
            "total_pnl": total_pnl,
            "pnl_by_asset": pnl_by_asset,
            "pnl_by_class": pnl_by_class
        }
    
    def _get_pricer(self, asset: AssetMetadata) -> AssetPricer:
        """Get appropriate pricer for asset class"""
        if asset.asset_class == AssetClass.STOCK:
            return StockPricer(asset)
        elif asset.asset_class == AssetClass.FUTURE:
            return FuturePricer(asset)
        elif asset.asset_class == AssetClass.OPTION:
            return OptionPricer(asset)
        elif asset.asset_class == AssetClass.CRYPTO:
            return CryptoPricer(asset)
        else:
            return AssetPricer(asset)
    
    def get_exposure_by_class(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """Get exposure breakdown by asset class"""
        exposure = {}
        
        for symbol, position in self.positions.items():
            asset = position["asset"]
            pricer = self._get_pricer(asset)
            
            current_price = current_prices.get(symbol, position["entry_price"])
            value = pricer.calculate_value(position["size"], current_price)
            
            asset_class = asset.asset_class.value
            exposure[asset_class] = exposure.get(asset_class, 0.0) + value
        
        return exposure


# Example asset definitions
EXAMPLE_ASSETS = [
    AssetMetadata(
        symbol="AAPL",
        asset_class=AssetClass.STOCK,
        exchange="NASDAQ",
        currency="USD",
        tick_size=0.01
    ),
    AssetMetadata(
        symbol="ESZ23",
        asset_class=AssetClass.FUTURE,
        exchange="CME",
        currency="USD",
        contract_size=50.0,
        tick_size=0.25
    ),
    AssetMetadata(
        symbol="AAPL_C_180_2024-03-15",
        asset_class=AssetClass.OPTION,
        exchange="CBOE",
        currency="USD",
        contract_size=100.0,
        tick_size=0.01
    ),
    AssetMetadata(
        symbol="BTC-USD",
        asset_class=AssetClass.CRYPTO,
        exchange="COINBASE",
        currency="USD",
        tick_size=0.01
    )
]
