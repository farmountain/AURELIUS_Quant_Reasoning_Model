"""
Strategy verification service for primitive API.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class StrategyVerifyRequest(BaseModel):
    """Request for strategy verification."""
    strategy_id: str
    strategy_type: str = Field(..., description="Type of strategy (momentum, mean_reversion, etc.)")
    parameters: Dict[str, Any] = Field(..., description="Strategy parameters to verify")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "momentum_001",
                "strategy_type": "momentum",
                "parameters": {
                    "lookback": 20,
                    "vol_target": 0.15,
                    "position_size": 0.25,
                    "stop_loss": 0.02,
                    "take_profit": 0.05
                },
                "context": {
                    "risk_preference": "moderate",
                    "instruments": ["SPY", "QQQ"]
                }
            }
        }


class ValidationCheck(BaseModel):
    """Individual validation check result."""
    check_name: str
    passed: bool
    severity: str  # "error", "warning", "info"
    message: str
    actual_value: Optional[Any] = None
    expected_range: Optional[str] = None


class StrategyVerifyResponse(BaseModel):
    """Response from strategy verification."""
    strategy_id: str
    valid: bool
    validation_score: float  # 0-100
    checks: List[ValidationCheck]
    issues: List[str]
    warnings: List[str]
    summary: str
    timestamp: str


class StrategyVerificationService:
    """Service for strategy configuration verification."""
    
    # Parameter validation rules by strategy type
    PARAM_RULES = {
        "momentum": {
            "lookback": {"min": 1, "max": 252, "type": "int"},
            "vol_target": {"min": 0.01, "max": 1.0, "type": "float"},
            "position_size": {"min": 0.01, "max": 1.0, "type": "float"},
            "stop_loss": {"min": 0.0, "max": 1.0, "type": "float", "optional": True},
            "take_profit": {"min": 0.0, "max": 1.0, "type": "float", "optional": True}
        },
        "mean_reversion": {
            "lookback": {"min": 2, "max": 252, "type": "int"},
            "entry_threshold": {"min": 0.5, "max": 5.0, "type": "float"},
            "exit_threshold": {"min": 0.1, "max": 2.0, "type": "float"},
            "vol_target": {"min": 0.01, "max": 1.0, "type": "float"},
            "position_size": {"min": 0.01, "max": 1.0, "type": "float"}
        },
        "trend_following": {
            "fast_window": {"min": 1, "max": 100, "type": "int"},
            "slow_window": {"min": 2, "max": 500, "type": "int"},
            "vol_target": {"min": 0.01, "max": 1.0, "type": "float"},
            "position_size": {"min": 0.01, "max": 1.0, "type": "float"}
        },
        "pairs_trading": {
            "lookback": {"min": 10, "max": 252, "type": "int"},
            "entry_z_score": {"min": 1.0, "max": 5.0, "type": "float"},
            "exit_z_score": {"min": 0.1, "max": 2.0, "type": "float"},
            "hedge_ratio": {"min": 0.5, "max": 2.0, "type": "float"},
            "position_size": {"min": 0.01, "max": 0.5, "type": "float"}
        },
        "volatility_trading": {
            "lookback": {"min": 5, "max": 100, "type": "int"},
            "vol_threshold": {"min": 0.05, "max": 2.0, "type": "float"},
            "position_size": {"min": 0.01, "max": 1.0, "type": "float"}
        },
        "ml_classifier": {
            "lookback": {"min": 10, "max": 252, "type": "int"},
            "prediction_threshold": {"min": 0.5, "max": 1.0, "type": "float"},
            "vol_target": {"min": 0.01, "max": 1.0, "type": "float"},
            "position_size": {"min": 0.01, "max": 1.0, "type": "float"}
        }
    }
    
    @staticmethod
    def verify_strategy(
        strategy_id: str,
        strategy_type: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> StrategyVerifyResponse:
        """
        Verify strategy configuration.
        
        Checks:
        1. Strategy type is valid
        2. Required parameters are present
        3. Parameter values are within valid ranges
        4. Parameter types are correct
        5. Business logic rules (e.g., fast_window < slow_window)
        """
        checks = []
        issues = []
        warnings = []
        
        # Check 1: Strategy type validity
        if strategy_type not in StrategyVerificationService.PARAM_RULES:
            checks.append(ValidationCheck(
                check_name="Strategy Type",
                passed=False,
                severity="error",
                message=f"Unknown strategy type '{strategy_type}'",
                actual_value=strategy_type,
                expected_range=f"One of: {', '.join(StrategyVerificationService.PARAM_RULES.keys())}"
            ))
            issues.append(f"Unknown strategy type: {strategy_type}")
        else:
            checks.append(ValidationCheck(
                check_name="Strategy Type",
                passed=True,
                severity="info",
                message=f"Strategy type '{strategy_type}' is valid"
            ))
        
        # Get rules for this strategy type
        rules = StrategyVerificationService.PARAM_RULES.get(strategy_type, {})
        
        # Check 2: Required parameters
        required_params = [k for k, v in rules.items() if not v.get("optional", False)]
        missing_params = [p for p in required_params if p not in parameters]
        
        if missing_params:
            checks.append(ValidationCheck(
                check_name="Required Parameters",
                passed=False,
                severity="error",
                message=f"Missing required parameters: {', '.join(missing_params)}",
                expected_range=f"Required: {', '.join(required_params)}"
            ))
            issues.extend([f"Missing parameter: {p}" for p in missing_params])
        else:
            checks.append(ValidationCheck(
                check_name="Required Parameters",
                passed=True,
                severity="info",
                message="All required parameters present"
            ))
        
        # Check 3 & 4: Parameter ranges and types
        for param_name, param_value in parameters.items():
            if param_name not in rules:
                checks.append(ValidationCheck(
                    check_name=f"Parameter: {param_name}",
                    passed=False,
                    severity="warning",
                    message=f"Unknown parameter '{param_name}' for strategy type '{strategy_type}'"
                ))
                warnings.append(f"Unknown parameter: {param_name}")
                continue
            
            rule = rules[param_name]
            expected_type = rule["type"]
            
            # Type check
            if expected_type == "int" and not isinstance(param_value, int):
                checks.append(ValidationCheck(
                    check_name=f"Parameter: {param_name} (type)",
                    passed=False,
                    severity="error",
                    message=f"Parameter '{param_name}' must be an integer",
                    actual_value=str(type(param_value).__name__),
                    expected_range="int"
                ))
                issues.append(f"Parameter '{param_name}' has wrong type (expected {expected_type})")
                continue
            
            if expected_type == "float" and not isinstance(param_value, (int, float)):
                checks.append(ValidationCheck(
                    check_name=f"Parameter: {param_name} (type)",
                    passed=False,
                    severity="error",
                    message=f"Parameter '{param_name}' must be a number",
                    actual_value=str(type(param_value).__name__),
                    expected_range="float"
                ))
                issues.append(f"Parameter '{param_name}' has wrong type (expected {expected_type})")
                continue
            
            # Range check
            min_val = rule.get("min")
            max_val = rule.get("max")
            
            range_str = f"{min_val} to {max_val}"
            if min_val is not None and param_value < min_val:
                checks.append(ValidationCheck(
                    check_name=f"Parameter: {param_name} (range)",
                    passed=False,
                    severity="error",
                    message=f"Parameter '{param_name}' value {param_value} is below minimum {min_val}",
                    actual_value=param_value,
                    expected_range=range_str
                ))
                issues.append(f"Parameter '{param_name}' value {param_value} is out of range ({range_str})")
            elif max_val is not None and param_value > max_val:
                checks.append(ValidationCheck(
                    check_name=f"Parameter: {param_name} (range)",
                    passed=False,
                    severity="error",
                    message=f"Parameter '{param_name}' value {param_value} exceeds maximum {max_val}",
                    actual_value=param_value,
                    expected_range=range_str
                ))
                issues.append(f"Parameter '{param_name}' value {param_value} is out of range ({range_str})")
            else:
                checks.append(ValidationCheck(
                    check_name=f"Parameter: {param_name} (range)",
                    passed=True,
                    severity="info",
                    message=f"Parameter '{param_name}' value {param_value} is within valid range",
                    actual_value=param_value,
                    expected_range=range_str
                ))
        
        # Check 5: Business logic rules
        if strategy_type == "trend_following":
            fast_window = parameters.get("fast_window")
            slow_window = parameters.get("slow_window")
            
            if fast_window and slow_window:
                if fast_window >= slow_window:
                    checks.append(ValidationCheck(
                        check_name="Business Logic: Window Ordering",
                        passed=False,
                        severity="error",
                        message="fast_window must be less than slow_window",
                        actual_value=f"fast={fast_window}, slow={slow_window}"
                    ))
                    issues.append("fast_window must be less than slow_window")
                else:
                    checks.append(ValidationCheck(
                        check_name="Business Logic: Window Ordering",
                        passed=True,
                        severity="info",
                        message="Window ordering is valid (fast < slow)"
                    ))
        
        if strategy_type == "mean_reversion":
            entry_threshold = parameters.get("entry_threshold")
            exit_threshold = parameters.get("exit_threshold")
            
            if entry_threshold and exit_threshold:
                if exit_threshold >= entry_threshold:
                    checks.append(ValidationCheck(
                        check_name="Business Logic: Threshold Ordering",
                        passed=False,
                        severity="error",
                        message="exit_threshold must be less than entry_threshold",
                        actual_value=f"entry={entry_threshold}, exit={exit_threshold}"
                    ))
                    issues.append("exit_threshold must be less than entry_threshold")
                else:
                    checks.append(ValidationCheck(
                        check_name="Business Logic: Threshold Ordering",
                        passed=True,
                        severity="info",
                        message="Threshold ordering is valid (exit < entry)"
                    ))
        
        # Check 6: Risk management consistency
        stop_loss = parameters.get("stop_loss")
        take_profit = parameters.get("take_profit")
        
        if stop_loss and take_profit:
            if stop_loss >= take_profit:
                checks.append(ValidationCheck(
                    check_name="Risk Management: Stop/Take Ratio",
                    passed=False,
                    severity="warning",
                    message="stop_loss should be less than take_profit for favorable risk/reward",
                    actual_value=f"stop={stop_loss}, take={take_profit}"
                ))
                warnings.append("stop_loss >= take_profit may indicate poor risk/reward ratio")
            else:
                checks.append(ValidationCheck(
                    check_name="Risk Management: Stop/Take Ratio",
                    passed=True,
                    severity="info",
                    message="Stop/take profit ratio is favorable"
                ))
        
        # Calculate validation score
        total_checks = len(checks)
        passed_checks = sum(1 for c in checks if c.passed)
        validation_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Overall validity (no errors)
        valid = len(issues) == 0
        
        # Generate summary
        if valid:
            summary = f"Strategy configuration is valid ({passed_checks}/{total_checks} checks passed)"
        else:
            summary = f"Strategy configuration has {len(issues)} error(s) and {len(warnings)} warning(s)"
        
        return StrategyVerifyResponse(
            strategy_id=strategy_id,
            valid=valid,
            validation_score=validation_score,
            checks=checks,
            issues=issues,
            warnings=warnings,
            summary=summary,
            timestamp=datetime.utcnow().isoformat()
        )
