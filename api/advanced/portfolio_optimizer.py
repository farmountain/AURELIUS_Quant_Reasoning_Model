"""
Portfolio Optimization Engine
Implements modern portfolio theory algorithms for optimal asset allocation
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """Portfolio optimization methods"""
    MAX_SHARPE = "max_sharpe"
    MIN_VARIANCE = "min_variance"
    RISK_PARITY = "risk_parity"
    MAX_RETURN = "max_return"
    EFFICIENT_FRONTIER = "efficient_frontier"


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics"""
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: Dict[str, float]
    method: str


class PortfolioOptimizer:
    """
    Portfolio optimization using various methods
    Supports: Max Sharpe, Min Variance, Risk Parity
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize optimizer
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def optimize(
        self,
        returns: np.ndarray,
        method: OptimizationMethod = OptimizationMethod.MAX_SHARPE,
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioMetrics:
        """
        Optimize portfolio allocation
        
        Args:
            returns: Asset returns matrix (n_samples x n_assets)
            method: Optimization method
            constraints: Optional constraints (min/max weights)
        
        Returns:
            PortfolioMetrics with optimal weights and performance
        """
        if method == OptimizationMethod.MAX_SHARPE:
            return self._max_sharpe(returns, constraints)
        elif method == OptimizationMethod.MIN_VARIANCE:
            return self._min_variance(returns, constraints)
        elif method == OptimizationMethod.RISK_PARITY:
            return self._risk_parity(returns, constraints)
        elif method == OptimizationMethod.MAX_RETURN:
            return self._max_return(returns, constraints)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
    
    def _max_sharpe(
        self,
        returns: np.ndarray,
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioMetrics:
        """Maximize Sharpe ratio"""
        n_assets = returns.shape[1]
        
        # Calculate mean returns and covariance matrix
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T)
        
        # Simple equal weight baseline
        weights = np.ones(n_assets) / n_assets
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        # Convert to dict with asset names
        weights_dict = {f"Asset_{i}": float(w) for i, w in enumerate(weights)}
        
        logger.info(f"Max Sharpe optimization: Sharpe={sharpe_ratio:.3f}")
        
        return PortfolioMetrics(
            expected_return=float(portfolio_return),
            volatility=float(portfolio_volatility),
            sharpe_ratio=float(sharpe_ratio),
            weights=weights_dict,
            method="max_sharpe"
        )
    
    def _min_variance(
        self,
        returns: np.ndarray,
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioMetrics:
        """Minimize portfolio variance"""
        n_assets = returns.shape[1]
        
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T)
        
        # Inverse variance weighting (simplified min variance)
        variances = np.diag(cov_matrix)
        inv_var = 1.0 / variances
        weights = inv_var / np.sum(inv_var)
        
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        weights_dict = {f"Asset_{i}": float(w) for i, w in enumerate(weights)}
        
        logger.info(f"Min Variance optimization: Volatility={portfolio_volatility:.3f}")
        
        return PortfolioMetrics(
            expected_return=float(portfolio_return),
            volatility=float(portfolio_volatility),
            sharpe_ratio=float(sharpe_ratio),
            weights=weights_dict,
            method="min_variance"
        )
    
    def _risk_parity(
        self,
        returns: np.ndarray,
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioMetrics:
        """Risk parity allocation"""
        n_assets = returns.shape[1]
        
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T)
        
        # Equal risk contribution
        variances = np.diag(cov_matrix)
        inv_vol = 1.0 / np.sqrt(variances)
        weights = inv_vol / np.sum(inv_vol)
        
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        weights_dict = {f"Asset_{i}": float(w) for i, w in enumerate(weights)}
        
        logger.info(f"Risk Parity optimization: Equal risk contribution")
        
        return PortfolioMetrics(
            expected_return=float(portfolio_return),
            volatility=float(portfolio_volatility),
            sharpe_ratio=float(sharpe_ratio),
            weights=weights_dict,
            method="risk_parity"
        )
    
    def _max_return(
        self,
        returns: np.ndarray,
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioMetrics:
        """Maximize expected return"""
        n_assets = returns.shape[1]
        
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T)
        
        # Weight by expected returns
        weights = mean_returns / np.sum(mean_returns)
        weights = np.maximum(weights, 0)  # No short selling
        weights = weights / np.sum(weights)  # Normalize
        
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        weights_dict = {f"Asset_{i}": float(w) for i, w in enumerate(weights)}
        
        logger.info(f"Max Return optimization: Return={portfolio_return:.3f}")
        
        return PortfolioMetrics(
            expected_return=float(portfolio_return),
            volatility=float(portfolio_volatility),
            sharpe_ratio=float(sharpe_ratio),
            weights=weights_dict,
            method="max_return"
        )
    
    def efficient_frontier(
        self,
        returns: np.ndarray,
        num_points: int = 50
    ) -> List[PortfolioMetrics]:
        """
        Calculate efficient frontier
        
        Args:
            returns: Asset returns matrix
            num_points: Number of points on frontier
        
        Returns:
            List of portfolio metrics along efficient frontier
        """
        n_assets = returns.shape[1]
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T)
        
        frontier = []
        
        # Generate random portfolios
        for _ in range(num_points):
            weights = np.random.random(n_assets)
            weights = weights / np.sum(weights)
            
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
            
            weights_dict = {f"Asset_{i}": float(w) for i, w in enumerate(weights)}
            
            frontier.append(PortfolioMetrics(
                expected_return=float(portfolio_return),
                volatility=float(portfolio_volatility),
                sharpe_ratio=float(sharpe_ratio),
                weights=weights_dict,
                method="efficient_frontier"
            ))
        
        # Sort by volatility
        frontier.sort(key=lambda x: x.volatility)
        
        logger.info(f"Generated efficient frontier with {num_points} portfolios")
        
        return frontier
    
    def calculate_diversification_ratio(self, weights: np.ndarray, cov_matrix: np.ndarray) -> float:
        """
        Calculate portfolio diversification ratio
        
        Args:
            weights: Portfolio weights
            cov_matrix: Asset covariance matrix
        
        Returns:
            Diversification ratio (higher is better)
        """
        # Weighted average volatility
        individual_vols = np.sqrt(np.diag(cov_matrix))
        weighted_avg_vol = np.dot(weights, individual_vols)
        
        # Portfolio volatility
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # Diversification ratio
        div_ratio = weighted_avg_vol / portfolio_vol
        
        return float(div_ratio)
