"""Risk validation service for primitive API."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class RiskThresholds(BaseModel):
    """Risk metric thresholds for validation."""
    min_sharpe: Optional[float] = Field(default=1.0, description="Minimum Sharpe ratio")
    min_sortino: Optional[float] = Field(default=1.2, description="Minimum Sortino ratio")
    max_drawdown: Optional[float] = Field(default=0.20, description="Maximum drawdown (0.20 = 20%)")
    max_var_95: Optional[float] = Field(default=-0.05, description="Maximum VaR at 95% confidence")
    max_var_99: Optional[float] = Field(default=-0.10, description="Maximum VaR at 99% confidence")
    min_calmar: Optional[float] = Field(default=0.5, description="Minimum Calmar ratio")
    max_volatility: Optional[float] = Field(default=0.30, description="Maximum annual volatility")


class RiskCheck(BaseModel):
    """Individual risk check result."""
    check_name: str
    passed: bool
    description: str
    actual_value: float
    threshold_value: float
    severity: str = "error"  # error, warning, info


class RiskValidateRequest(BaseModel):
    """Request for risk validation."""
    strategy_id: str
    metrics: Dict[str, float] = Field(..., description="Risk metrics to validate")
    thresholds: Optional[RiskThresholds] = Field(default=None, description="Custom thresholds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "momentum_v1",
                "metrics": {
                    "sharpe_ratio": 1.5,
                    "sortino_ratio": 1.8,
                    "max_drawdown": 0.15,
                    "var_95": -0.03,
                    "var_99": -0.06,
                    "calmar_ratio": 0.8,
                    "volatility": 0.25
                },
                "thresholds": {
                    "min_sharpe": 1.0,
                    "max_drawdown": 0.20
                }
            }
        }


class RiskValidateResponse(BaseModel):
    """Response for risk validation."""
    strategy_id: str
    passed: bool
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    checks: List[RiskCheck]
    recommendations: List[str]
    summary: str


class RiskValidationService:
    """Service for risk metric validation."""
    
    # Default thresholds
    DEFAULT_THRESHOLDS = RiskThresholds()
    
    @staticmethod
    def validate_risk_metrics(
        strategy_id: str,
        metrics: Dict[str, float],
        thresholds: Optional[RiskThresholds] = None
    ) -> RiskValidateResponse:
        """
        Validate risk metrics against thresholds.
        
        Args:
            strategy_id: Strategy identifier
            metrics: Risk metrics to validate
            thresholds: Custom thresholds (uses defaults if None)
        
        Returns:
            RiskValidateResponse with validation results
        """
        # Use default thresholds if not provided
        thresh = thresholds or RiskValidationService.DEFAULT_THRESHOLDS
        
        checks = []
        
        # Check 1: Sharpe ratio
        sharpe = metrics.get("sharpe_ratio", 0.0)
        if thresh.min_sharpe is not None:
            sharpe_pass = sharpe >= thresh.min_sharpe
            checks.append(RiskCheck(
                check_name="Sharpe Ratio",
                passed=sharpe_pass,
                description=f"Sharpe ratio must be >= {thresh.min_sharpe}",
                actual_value=sharpe,
                threshold_value=thresh.min_sharpe,
                severity="error" if not sharpe_pass else "info"
            ))
        
        # Check 2: Sortino ratio
        sortino = metrics.get("sortino_ratio", 0.0)
        if thresh.min_sortino is not None:
            sortino_pass = sortino >= thresh.min_sortino
            checks.append(RiskCheck(
                check_name="Sortino Ratio",
                passed=sortino_pass,
                description=f"Sortino ratio must be >= {thresh.min_sortino}",
                actual_value=sortino,
                threshold_value=thresh.min_sortino,
                severity="error" if not sortino_pass else "info"
            ))
        
        # Check 3: Max drawdown
        max_dd = metrics.get("max_drawdown", 1.0)
        if thresh.max_drawdown is not None:
            dd_pass = max_dd <= thresh.max_drawdown
            checks.append(RiskCheck(
                check_name="Max Drawdown",
                passed=dd_pass,
                description=f"Max drawdown must be <= {thresh.max_drawdown:.1%}",
                actual_value=max_dd,
                threshold_value=thresh.max_drawdown,
                severity="error" if not dd_pass else "info"
            ))
        
        # Check 4: VaR 95%
        var_95 = metrics.get("var_95", 0.0)
        if thresh.max_var_95 is not None:
            # VaR is negative, so "less risky" means greater value (closer to 0)
            var_95_pass = var_95 >= thresh.max_var_95
            checks.append(RiskCheck(
                check_name="Value at Risk (95%)",
                passed=var_95_pass,
                description=f"VaR 95% must be >= {thresh.max_var_95:.2%}",
                actual_value=var_95,
                threshold_value=thresh.max_var_95,
                severity="warning" if not var_95_pass else "info"
            ))
        
        # Check 5: VaR 99%
        var_99 = metrics.get("var_99", 0.0)
        if thresh.max_var_99 is not None:
            var_99_pass = var_99 >= thresh.max_var_99
            checks.append(RiskCheck(
                check_name="Value at Risk (99%)",
                passed=var_99_pass,
                description=f"VaR 99% must be >= {thresh.max_var_99:.2%}",
                actual_value=var_99,
                threshold_value=thresh.max_var_99,
                severity="warning" if not var_99_pass else "info"
            ))
        
        # Check 6: Calmar ratio
        calmar = metrics.get("calmar_ratio", 0.0)
        if thresh.min_calmar is not None:
            calmar_pass = calmar >= thresh.min_calmar
            checks.append(RiskCheck(
                check_name="Calmar Ratio",
                passed=calmar_pass,
                description=f"Calmar ratio must be >= {thresh.min_calmar}",
                actual_value=calmar,
                threshold_value=thresh.min_calmar,
                severity="warning" if not calmar_pass else "info"
            ))
        
        # Check 7: Volatility
        volatility = metrics.get("volatility", 0.0)
        if thresh.max_volatility is not None:
            vol_pass = volatility <= thresh.max_volatility
            checks.append(RiskCheck(
                check_name="Volatility",
                passed=vol_pass,
                description=f"Annual volatility must be <= {thresh.max_volatility:.1%}",
                actual_value=volatility,
                threshold_value=thresh.max_volatility,
                severity="warning" if not vol_pass else "info"
            ))
        
        # Calculate overall status
        error_checks = [c for c in checks if c.severity == "error"]
        passed = all(c.passed for c in error_checks) if error_checks else all(c.passed for c in checks)
        
        # Calculate risk score (0-100)
        if checks:
            passed_count = sum(1 for c in checks if c.passed)
            risk_score = (passed_count / len(checks)) * 100
        else:
            risk_score = 100.0
        
        # Generate recommendations
        recommendations = []
        for check in checks:
            if not check.passed and check.severity == "error":
                recommendations.append(
                    f"Improve {check.check_name}: current {check.actual_value:.2f}, "
                    f"target {check.threshold_value:.2f}"
                )
        
        if not recommendations:
            for check in checks:
                if not check.passed and check.severity == "warning":
                    recommendations.append(
                        f"Consider improving {check.check_name}: current {check.actual_value:.2f}"
                    )
        
        # Generate summary
        failed_critical = [c for c in checks if not c.passed and c.severity == "error"]
        if passed:
            summary = f"All critical risk checks passed ({len(checks)} checks evaluated)"
        else:
            summary = f"{len(failed_critical)} critical risk check(s) failed"
        
        return RiskValidateResponse(
            strategy_id=strategy_id,
            passed=passed,
            risk_score=round(risk_score, 1),
            checks=checks,
            recommendations=recommendations,
            summary=summary
        )
