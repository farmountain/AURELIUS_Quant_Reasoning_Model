"""
Advanced Risk Metrics Calculator
VaR, CVaR, Sortino, Calmar, Maximum Drawdown, and more
"""
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for a strategy or portfolio"""
    # Volatility metrics
    volatility: float
    downside_deviation: float
    
    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Drawdown metrics
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    
    # Value at Risk
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float
    
    # Additional metrics
    skewness: float
    kurtosis: float
    tail_ratio: float


class RiskAnalyzer:
    """
    Advanced risk analytics for trading strategies
    Calculates comprehensive risk metrics
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize risk analyzer
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_all_metrics(
        self,
        returns: np.ndarray,
        equity_curve: Optional[np.ndarray] = None
    ) -> RiskMetrics:
        """
        Calculate all risk metrics
        
        Args:
            returns: Array of returns
            equity_curve: Optional equity curve for drawdown calculations
        
        Returns:
            RiskMetrics dataclass with all calculated metrics
        """
        if equity_curve is None:
            equity_curve = np.cumprod(1 + returns)
        
        return RiskMetrics(
            volatility=self.calculate_volatility(returns),
            downside_deviation=self.calculate_downside_deviation(returns),
            sharpe_ratio=self.calculate_sharpe_ratio(returns),
            sortino_ratio=self.calculate_sortino_ratio(returns),
            calmar_ratio=self.calculate_calmar_ratio(returns, equity_curve),
            max_drawdown=self.calculate_max_drawdown(equity_curve),
            max_drawdown_duration=self.calculate_max_drawdown_duration(equity_curve),
            avg_drawdown=self.calculate_avg_drawdown(equity_curve),
            var_95=self.calculate_var(returns, confidence=0.95),
            var_99=self.calculate_var(returns, confidence=0.99),
            cvar_95=self.calculate_cvar(returns, confidence=0.95),
            cvar_99=self.calculate_cvar(returns, confidence=0.99),
            skewness=self.calculate_skewness(returns),
            kurtosis=self.calculate_kurtosis(returns),
            tail_ratio=self.calculate_tail_ratio(returns),
        )
    
    def calculate_volatility(self, returns: np.ndarray, annualize: bool = True) -> float:
        """Calculate annualized volatility"""
        vol = np.std(returns)
        if annualize:
            vol = vol * np.sqrt(252)  # Assuming daily returns
        return float(vol)
    
    def calculate_downside_deviation(self, returns: np.ndarray, threshold: float = 0.0) -> float:
        """Calculate downside deviation (semideviation)"""
        downside_returns = returns[returns < threshold]
        if len(downside_returns) == 0:
            return 0.0
        return float(np.std(downside_returns) * np.sqrt(252))
    
    def calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - (self.risk_free_rate / 252)
        if np.std(returns) == 0:
            return 0.0
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))
    
    def calculate_sortino_ratio(self, returns: np.ndarray, threshold: float = 0.0) -> float:
        """Calculate Sortino ratio"""
        excess_returns = returns - (self.risk_free_rate / 252)
        downside_dev = self.calculate_downside_deviation(returns, threshold) / np.sqrt(252)
        if downside_dev == 0:
            return 0.0
        return float(np.mean(excess_returns) / downside_dev * np.sqrt(252))
    
    def calculate_max_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        return float(np.min(drawdown))
    
    def calculate_max_drawdown_duration(self, equity_curve: np.ndarray) -> int:
        """Calculate maximum drawdown duration in days"""
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        
        # Find drawdown periods
        is_drawdown = drawdown < 0
        if not np.any(is_drawdown):
            return 0
        
        # Calculate duration of each drawdown
        durations = []
        current_duration = 0
        
        for dd in is_drawdown:
            if dd:
                current_duration += 1
            else:
                if current_duration > 0:
                    durations.append(current_duration)
                    current_duration = 0
        
        if current_duration > 0:
            durations.append(current_duration)
        
        return int(max(durations)) if durations else 0
    
    def calculate_avg_drawdown(self, equity_curve: np.ndarray) -> float:
        """Calculate average drawdown"""
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        negative_drawdowns = drawdown[drawdown < 0]
        if len(negative_drawdowns) == 0:
            return 0.0
        return float(np.mean(negative_drawdowns))
    
    def calculate_calmar_ratio(self, returns: np.ndarray, equity_curve: np.ndarray) -> float:
        """Calculate Calmar ratio (return / max drawdown)"""
        annual_return = np.mean(returns) * 252
        max_dd = abs(self.calculate_max_drawdown(equity_curve))
        if max_dd == 0:
            return 0.0
        return float(annual_return / max_dd)
    
    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)
        
        Args:
            returns: Array of returns
            confidence: Confidence level (0.95 or 0.99)
        
        Returns:
            VaR at specified confidence level
        """
        return float(np.percentile(returns, (1 - confidence) * 100))
    
    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall)
        
        Args:
            returns: Array of returns
            confidence: Confidence level (0.95 or 0.99)
        
        Returns:
            CVaR at specified confidence level
        """
        var = self.calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]
        if len(tail_returns) == 0:
            return var
        return float(np.mean(tail_returns))
    
    def calculate_skewness(self, returns: np.ndarray) -> float:
        """Calculate return skewness"""
        from scipy import stats
        return float(stats.skew(returns))
    
    def calculate_kurtosis(self, returns: np.ndarray) -> float:
        """Calculate return kurtosis (excess kurtosis)"""
        from scipy import stats
        return float(stats.kurtosis(returns))
    
    def calculate_tail_ratio(self, returns: np.ndarray) -> float:
        """
        Calculate tail ratio (right tail / left tail)
        Values > 1 indicate positive asymmetry
        """
        right_tail = np.percentile(returns, 95)
        left_tail = abs(np.percentile(returns, 5))
        if left_tail == 0:
            return 0.0
        return float(right_tail / left_tail)
    
    def calculate_information_ratio(
        self,
        returns: np.ndarray,
        benchmark_returns: np.ndarray
    ) -> float:
        """Calculate information ratio vs benchmark"""
        active_returns = returns - benchmark_returns
        if np.std(active_returns) == 0:
            return 0.0
        return float(np.mean(active_returns) / np.std(active_returns) * np.sqrt(252))
    
    def calculate_beta(
        self,
        returns: np.ndarray,
        market_returns: np.ndarray
    ) -> float:
        """Calculate portfolio beta"""
        covariance = np.cov(returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        if market_variance == 0:
            return 0.0
        return float(covariance / market_variance)
    
    def calculate_alpha(
        self,
        returns: np.ndarray,
        market_returns: np.ndarray,
        beta: Optional[float] = None
    ) -> float:
        """Calculate Jensen's alpha"""
        if beta is None:
            beta = self.calculate_beta(returns, market_returns)
        
        portfolio_return = np.mean(returns) * 252
        market_return = np.mean(market_returns) * 252
        
        expected_return = self.risk_free_rate + beta * (market_return - self.risk_free_rate)
        alpha = portfolio_return - expected_return
        
        return float(alpha)


def format_risk_metrics(metrics: RiskMetrics) -> Dict[str, Any]:
    """Format risk metrics for API response"""
    return {
        "volatility": {
            "annual_volatility": round(metrics.volatility * 100, 2),
            "downside_deviation": round(metrics.downside_deviation * 100, 2),
        },
        "risk_adjusted_returns": {
            "sharpe_ratio": round(metrics.sharpe_ratio, 3),
            "sortino_ratio": round(metrics.sortino_ratio, 3),
            "calmar_ratio": round(metrics.calmar_ratio, 3),
        },
        "drawdown": {
            "max_drawdown": round(metrics.max_drawdown * 100, 2),
            "max_drawdown_duration_days": metrics.max_drawdown_duration,
            "avg_drawdown": round(metrics.avg_drawdown * 100, 2),
        },
        "value_at_risk": {
            "var_95": round(metrics.var_95 * 100, 2),
            "var_99": round(metrics.var_99 * 100, 2),
            "cvar_95": round(metrics.cvar_95 * 100, 2),
            "cvar_99": round(metrics.cvar_99 * 100, 2),
        },
        "distribution": {
            "skewness": round(metrics.skewness, 3),
            "kurtosis": round(metrics.kurtosis, 3),
            "tail_ratio": round(metrics.tail_ratio, 3),
        },
    }
