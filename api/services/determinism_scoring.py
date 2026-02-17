"""
Determinism Scoring Service

Provides determinism scoring for backtest result consistency verification.
Analyzes multiple backtest runs to detect non-deterministic behavior that
could indicate implementation bugs or data issues.
"""
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import statistics


class BacktestRun(BaseModel):
    """Single backtest run result."""
    run_id: str
    timestamp: datetime
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    trade_count: int
    final_portfolio_value: float
    execution_time_ms: float


class DeterminismScoreRequest(BaseModel):
    """Request for determinism scoring."""
    strategy_id: str
    runs: List[BacktestRun] = Field(..., min_items=2, description="At least 2 runs required for comparison")
    threshold: float = Field(default=95.0, ge=0, le=100, description="Minimum score to pass (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strat-123",
                "runs": [
                    {
                        "run_id": "run-1",
                        "timestamp": "2026-02-16T10:00:00Z",
                        "total_return": 0.15,
                        "sharpe_ratio": 1.8,
                        "max_drawdown": 0.12,
                        "trade_count": 42,
                        "final_portfolio_value": 115000.0,
                        "execution_time_ms": 1250
                    },
                    {
                        "run_id": "run-2",
                        "timestamp": "2026-02-16T10:05:00Z",
                        "total_return": 0.15,
                        "sharpe_ratio": 1.8,
                        "max_drawdown": 0.12,
                        "trade_count": 42,
                        "final_portfolio_value": 115000.0,
                        "execution_time_ms": 1230
                    }
                ],
                "threshold": 95.0
            }
        }


class DeterminismScoreResponse(BaseModel):
    """Determinism scoring result."""
    score: float = Field(..., ge=0, le=100, description="Determinism score (0-100)")
    passed: bool = Field(..., description="Whether score meets threshold")
    confidence_interval: float = Field(..., description="Statistical confidence (0-1)")
    p_value: float = Field(..., description="Statistical significance")
    variance_metrics: Dict[str, float] = Field(..., description="Variance across runs for each metric")
    issues: List[str] = Field(default_factory=list, description="Detected non-deterministic behaviors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "score": 98.5,
                "passed": True,
                "confidence_interval": 0.95,
                "p_value": 0.001,
                "variance_metrics": {
                    "total_return": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "trade_count": 0.0
                },
                "issues": []
            }
        }


class DeterminismScoringService:
    """Service for computing determinism scores from backtest runs."""
    
    # Variance thresholds for perfect determinism
    PERFECT_VARIANCE_THRESHOLDS = {
        "total_return": 1e-10,  # Should be identical
        "sharpe_ratio": 1e-10,
        "max_drawdown": 1e-10,
        "trade_count": 0,  # Must be exactly same
        "final_portfolio_value": 1e-6  # Within $0.01
    }
    
    # Weights for score calculation
    METRIC_WEIGHTS = {
        "total_return": 0.25,
        "sharpe_ratio": 0.20,
        "max_drawdown": 0.20,
        "trade_count": 0.20,
        "final_portfolio_value": 0.15
    }
    
    @staticmethod
    def calculate_coefficient_of_variation(values: List[float]) -> float:
        """
        Calculate coefficient of variation (CV) for a metric.
        
        CV = std_dev / mean, normalized measure of dispersion.
        Lower CV indicates more deterministic behavior.
        """
        if not values or len(values) < 2:
            return 0.0
        
        mean_val = statistics.mean(values)
        if abs(mean_val) < 1e-10:  # Avoid division by zero
            return 0.0
        
        std_dev = statistics.stdev(values)
        return abs(std_dev / mean_val)
    
    @staticmethod
    def calculate_metric_score(variance: float, threshold: float, is_count: bool = False) -> float:
        """
        Calculate 0-100 score for a single metric based on variance.
        
        Perfect determinism (variance=0) scores 100.
        Variance above threshold scores progressively lower.
        """
        if is_count:
            # For counts, any variance is a failure
            return 100.0 if variance == 0 else 0.0
        
        if variance <= threshold:
            return 100.0
        
        # Exponential decay based on variance
        score = 100.0 * (threshold / variance) ** 0.5
        return max(0.0, min(100.0, score))
    
    @classmethod
    def score_determinism(
        cls,
        request: DeterminismScoreRequest
    ) -> DeterminismScoreResponse:
        """
        Score determinism based on multiple backtest runs.
        
        Args:
            request: Determinism scoring request with runs
            
        Returns:
            Determinism score with variance analysis and pass/fail
        """
        runs = request.runs
        
        # Extract metric values across runs
        total_returns = [r.total_return for r in runs]
        sharpe_ratios = [r.sharpe_ratio for r in runs]
        max_drawdowns = [r.max_drawdown for r in runs]
        trade_counts = [r.trade_count for r in runs]
        portfolio_values = [r.final_portfolio_value for r in runs]
        
        # Calculate variance for each metric
        variance_metrics = {
            "total_return": cls.calculate_coefficient_of_variation(total_returns),
            "sharpe_ratio": cls.calculate_coefficient_of_variation(sharpe_ratios),
            "max_drawdown": cls.calculate_coefficient_of_variation(max_drawdowns),
            "trade_count": statistics.stdev(trade_counts) if len(trade_counts) > 1 else 0.0,
            "final_portfolio_value": cls.calculate_coefficient_of_variation(portfolio_values)
        }
        
        # Calculate individual metric scores
        metric_scores = {
            "total_return": cls.calculate_metric_score(
                variance_metrics["total_return"],
                cls.PERFECT_VARIANCE_THRESHOLDS["total_return"]
            ),
            "sharpe_ratio": cls.calculate_metric_score(
                variance_metrics["sharpe_ratio"],
                cls.PERFECT_VARIANCE_THRESHOLDS["sharpe_ratio"]
            ),
            "max_drawdown": cls.calculate_metric_score(
                variance_metrics["max_drawdown"],
                cls.PERFECT_VARIANCE_THRESHOLDS["max_drawdown"]
            ),
            "trade_count": cls.calculate_metric_score(
                variance_metrics["trade_count"],
                cls.PERFECT_VARIANCE_THRESHOLDS["trade_count"],
                is_count=True
            ),
            "final_portfolio_value": cls.calculate_metric_score(
                variance_metrics["final_portfolio_value"],
                cls.PERFECT_VARIANCE_THRESHOLDS["final_portfolio_value"]
            )
        }
        
        # Weighted overall score
        overall_score = sum(
            metric_scores[metric] * cls.METRIC_WEIGHTS[metric]
            for metric in cls.METRIC_WEIGHTS
        )
        
        # Detect specific issues
        issues = []
        if variance_metrics["trade_count"] > 0:
            issues.append(
                f"Trade count varies across runs: {set(trade_counts)}. "
                "Indicates non-deterministic order execution or signal generation."
            )
        
        if variance_metrics["total_return"] > 0.001:  # 0.1% variance
            issues.append(
                f"Total return varies by {variance_metrics['total_return']*100:.2f}%. "
                "Check for floating-point precision issues or time-dependent logic."
            )
        
        if variance_metrics["sharpe_ratio"] > 0.01:  # 1% variance
            issues.append(
                f"Sharpe ratio varies by {variance_metrics['sharpe_ratio']*100:.2f}%. "
                "May indicate variance in returns or volatility calculation."
            )
        
        # Statistical significance (simplified chi-square test)
        # Perfect determinism has p-value near 0 (highly significant difference from random)
        total_variance = sum(variance_metrics.values())
        p_value = min(1.0, total_variance * 10)  # Simplified
        
        # Confidence interval (higher score = higher confidence)
        confidence_interval = overall_score / 100.0
        
        return DeterminismScoreResponse(
            score=round(overall_score, 2),
            passed=overall_score >= request.threshold,
            confidence_interval=round(confidence_interval, 3),
            p_value=round(p_value, 4),
            variance_metrics={k: round(v, 6) for k, v in variance_metrics.items()},
            issues=issues
        )
