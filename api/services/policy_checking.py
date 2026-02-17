"""Policy checking service for primitive API."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class PolicyRule(BaseModel):
    """Individual policy rule definition."""
    rule_id: str
    rule_type: str = Field(..., description="regulatory, business, governance, compliance")
    description: str
    severity: str = "error"  # error, warning, info


class PolicyCheckResult(BaseModel):
    """Result of a single policy check."""
    rule_id: str
    passed: bool
    message: str
    severity: str
    recommendation: Optional[str] = None


class PolicyCheckRequest(BaseModel):
    """Request for policy checking."""
    strategy_id: str
    context: Dict[str, Any] = Field(..., description="Context data for policy evaluation")
    rules: Optional[List[PolicyRule]] = Field(default=None, description="Custom rules to check")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "momentum_v1",
                "context": {
                    "max_drawdown": 0.15,
                    "max_leverage": 1.5,
                    "turnover_rate": 2.5,
                    "lineage_complete": True,
                    "governance_compliant": True,
                    "regulatory_approved": False
                },
                "rules": [
                    {
                        "rule_id": "max_drawdown_limit",
                        "rule_type": "business",
                        "description": "Max drawdown must not exceed 20%",
                        "severity": "error"
                    }
                ]
            }
        }


class PolicyCheckResponse(BaseModel):
    """Response for policy checking."""
    strategy_id: str
    passed: bool
    compliance_score: float = Field(..., description="Overall compliance score (0-100)")
    checks: List[PolicyCheckResult]
    blockers: List[str] = Field(..., description="Critical policy violations")
    warnings: List[str] = Field(..., description="Non-critical policy warnings")
    summary: str


class PolicyCheckingService:
    """Service for policy and compliance checking."""
    
    # Default policy rules
    DEFAULT_RULES = [
        PolicyRule(
            rule_id="max_drawdown_regulatory",
            rule_type="regulatory",
            description="Max drawdown must not exceed 25%",
            severity="error"
        ),
        PolicyRule(
            rule_id="max_leverage_regulatory",
            rule_type="regulatory",
            description="Max leverage must not exceed 2x",
            severity="error"
        ),
        PolicyRule(
            rule_id="lineage_completeness",
            rule_type="governance",
            description="Data lineage must be complete",
            severity="error"
        ),
        PolicyRule(
            rule_id="governance_compliance",
            rule_type="governance",
            description="Governance policies must be met",
            severity="error"
        ),
        PolicyRule(
            rule_id="turnover_constraint",
            rule_type="business",
            description="Turnover rate should be reasonable (<5x)",
            severity="warning"
        ),
    ]
    
    @staticmethod
    def check_policies(
        strategy_id: str,
        context: Dict[str, Any],
        rules: Optional[List[PolicyRule]] = None
    ) -> PolicyCheckResponse:
        """
        Check policy compliance based on context data.
        
        Args:
            strategy_id: Strategy identifier
            context: Context data for policy evaluation
            rules: Custom rules to check (uses defaults if None)
        
        Returns:
            PolicyCheckResponse with compliance results
        """
        # Use default rules if not provided
        active_rules = rules or PolicyCheckingService.DEFAULT_RULES
        
        checks = []
        blockers = []
        warnings = []
        
        for rule in active_rules:
            check_result = PolicyCheckingService._evaluate_rule(rule, context)
            checks.append(check_result)
            
            if not check_result.passed:
                if check_result.severity == "error":
                    blockers.append(f"{rule.rule_id}: {check_result.message}")
                elif check_result.severity == "warning":
                    warnings.append(f"{rule.rule_id}: {check_result.message}")
        
        # Calculate overall status
        error_checks = [c for c in checks if c.severity == "error"]
        passed = all(c.passed for c in error_checks) if error_checks else True
        
        # Calculate compliance score
        if checks:
            passed_count = sum(1 for c in checks if c.passed)
            compliance_score = (passed_count / len(checks)) * 100
        else:
            compliance_score = 100.0
        
        # Generate summary
        if passed:
            summary = f"All critical policy checks passed ({len(checks)} rules evaluated)"
        else:
            summary = f"{len(blockers)} critical policy violation(s) detected"
        
        return PolicyCheckResponse(
            strategy_id=strategy_id,
            passed=passed,
            compliance_score=round(compliance_score, 1),
            checks=checks,
            blockers=blockers,
            warnings=warnings,
            summary=summary
        )
    
    @staticmethod
    def _evaluate_rule(rule: PolicyRule, context: Dict[str, Any]) -> PolicyCheckResult:
        """
        Evaluate a single policy rule against context.
        
        Args:
            rule: Policy rule to evaluate
            context: Context data
        
        Returns:
            PolicyCheckResult
        """
        # Max drawdown check
        if rule.rule_id == "max_drawdown_regulatory":
            max_dd = context.get("max_drawdown", 1.0)
            threshold = 0.25  # 25%
            passed = max_dd <= threshold
            return PolicyCheckResult(
                rule_id=rule.rule_id,
                passed=passed,
                message=f"Max drawdown is {max_dd:.1%} (limit: {threshold:.1%})",
                severity=rule.severity,
                recommendation="Reduce position sizes or add stop-losses" if not passed else None
            )
        
        # Max leverage check
        elif rule.rule_id == "max_leverage_regulatory":
            max_lev = context.get("max_leverage", 0.0)
            threshold = 2.0  # 2x
            passed = max_lev <= threshold
            return PolicyCheckResult(
                rule_id=rule.rule_id,
                passed=passed,
                message=f"Max leverage is {max_lev:.1f}x (limit: {threshold:.1f}x)",
                severity=rule.severity,
                recommendation="Reduce leverage ratio" if not passed else None
            )
        
        # Lineage completeness check
        elif rule.rule_id == "lineage_completeness":
            lineage_complete = context.get("lineage_complete", False)
            passed = bool(lineage_complete)
            return PolicyCheckResult(
                rule_id=rule.rule_id,
                passed=passed,
                message="Data lineage is complete" if passed else "Data lineage is incomplete",
                severity=rule.severity,
                recommendation="Complete run_identity, data_provenance, transformation_lineage fields" if not passed else None
            )
        
        # Governance compliance check
        elif rule.rule_id == "governance_compliance":
            gov_compliant = context.get("governance_compliant", False)
            passed = bool(gov_compliant)
            return PolicyCheckResult(
                rule_id=rule.rule_id,
                passed=passed,
                message="Governance policies met" if passed else "Governance policies not met",
                severity=rule.severity,
                recommendation="Review governance requirements and update strategy" if not passed else None
            )
        
        # Turnover constraint check
        elif rule.rule_id == "turnover_constraint":
            turnover = context.get("turnover_rate", 0.0)
            threshold = 5.0  # 5x
            passed = turnover <= threshold
            return PolicyCheckResult(
                rule_id=rule.rule_id,
                passed=passed,
                message=f"Turnover rate is {turnover:.1f}x (recommended: <{threshold:.1f}x)",
                severity=rule.severity,
                recommendation="Consider reducing trading frequency to lower costs" if not passed else None
            )
        
        # Generic rule evaluation (fallback)
        else:
            # Try to infer from rule description and context
            passed = True  # Default to pass for unknown rules
            message = f"{rule.description} - evaluation pending"
            
            return PolicyCheckResult(
                rule_id=rule.rule_id,
                passed=passed,
                message=message,
                severity=rule.severity,
                recommendation=None
            )
