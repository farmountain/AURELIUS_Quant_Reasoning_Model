"""Reflexion loop for failure handling and repair."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from aureus.gates.base import GateResult


@dataclass
class RepairPlan:
    """Plan for repairing a failure."""
    
    failure_type: str
    description: str
    actions: List[str]
    retry_state: str


class ReflexionLoop:
    """Reflexion loop that generates repair plans for failures."""
    
    def __init__(self, max_retries: int = 3):
        """Initialize reflexion loop.
        
        Args:
            max_retries: Maximum number of repair attempts
        """
        self.max_retries = max_retries
        self.attempt_count = 0
    
    def analyze_failure(self, gate_result: GateResult) -> RepairPlan:
        """Analyze a gate failure and generate a repair plan.
        
        Args:
            gate_result: The failed gate result
            
        Returns:
            RepairPlan with suggested actions
        """
        failure_type = self._classify_failure(gate_result)
        
        if failure_type == "test_failure":
            return RepairPlan(
                failure_type=failure_type,
                description="Tests failed - code quality issues detected",
                actions=[
                    "Review test failures in gate details",
                    "Fix failing tests",
                    "Re-run dev gate",
                ],
                retry_state="dev_gate",
            )
        
        elif failure_type == "determinism_failure":
            return RepairPlan(
                failure_type=failure_type,
                description="Determinism check failed - non-deterministic behavior detected",
                actions=[
                    "Check for unseeded random number generators",
                    "Verify no system time dependencies",
                    "Ensure all operations are reproducible",
                    "Re-run determinism check",
                ],
                retry_state="dev_gate",
            )
        
        elif failure_type == "lint_failure":
            return RepairPlan(
                failure_type=failure_type,
                description="Lint check failed - code style issues detected",
                actions=[
                    "Review lint errors in gate details",
                    "Fix clippy warnings",
                    "Re-run lint check",
                ],
                retry_state="dev_gate",
            )
        
        elif failure_type == "crv_failure":
            return RepairPlan(
                failure_type=failure_type,
                description="CRV verification failed - strategy violates constraints",
                actions=[
                    "Review CRV violations",
                    "Adjust strategy parameters to meet constraints",
                    "Re-run backtest",
                    "Re-run product gate",
                ],
                retry_state="backtest",
            )
        
        else:
            return RepairPlan(
                failure_type="unknown",
                description="Unknown failure type",
                actions=[
                    "Review error messages",
                    "Check logs for details",
                    "Consider manual intervention",
                ],
                retry_state="init",
            )
    
    def _classify_failure(self, gate_result: GateResult) -> str:
        """Classify the type of failure.
        
        Args:
            gate_result: The failed gate result
            
        Returns:
            Failure type string
        """
        checks = gate_result.checks
        
        if not checks.get("tests_pass", True):
            return "test_failure"
        
        if not checks.get("determinism", True):
            return "determinism_failure"
        
        if not checks.get("lint", True):
            return "lint_failure"
        
        if not checks.get("crv_pass", True):
            return "crv_failure"
        
        return "unknown"
    
    def should_retry(self) -> bool:
        """Check if we should retry after a failure.
        
        Returns:
            True if we should retry, False otherwise
        """
        return self.attempt_count < self.max_retries
    
    def increment_attempt(self) -> None:
        """Increment the attempt counter."""
        self.attempt_count += 1
    
    def reset(self) -> None:
        """Reset the reflexion loop."""
        self.attempt_count = 0
    
    def generate_failure_summary(self, gate_result: GateResult) -> str:
        """Generate a human-readable failure summary.
        
        Args:
            gate_result: The failed gate result
            
        Returns:
            Failure summary string
        """
        lines = [
            "=== Failure Summary ===",
            f"Gate Result: {gate_result}",
            "",
            "Failed Checks:",
        ]
        
        for check_name, passed in gate_result.checks.items():
            status = "✓" if passed else "✗"
            lines.append(f"  {status} {check_name}")
        
        if gate_result.errors:
            lines.append("")
            lines.append("Errors:")
            for error in gate_result.errors:
                lines.append(f"  - {error}")
        
        return "\n".join(lines)
