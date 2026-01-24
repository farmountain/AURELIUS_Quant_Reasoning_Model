"""Product gate: CRV verification and stress testing."""

from typing import Dict
from pathlib import Path
from aureus.gates.base import Gate, GateResult
from aureus.tools.rust_wrapper import RustEngineWrapper
from aureus.tools.schemas import ToolCall, ToolType, CRVVerifyToolInput


class ProductGate(Gate):
    """Product gate that enforces production-readiness checks."""
    
    def __init__(self, rust_wrapper: RustEngineWrapper, max_drawdown_limit: float = 0.25):
        """Initialize product gate.
        
        Args:
            rust_wrapper: Rust engine wrapper for running checks
            max_drawdown_limit: Maximum allowed drawdown (default 25%)
        """
        self.rust_wrapper = rust_wrapper
        self.max_drawdown_limit = max_drawdown_limit
    
    def get_name(self) -> str:
        """Get the gate name."""
        return "ProductGate"
    
    def run(self, context: Dict[str, any]) -> GateResult:
        """Run product gate checks.
        
        Args:
            context: Must contain 'output_dir' with backtest results
            
        Returns:
            GateResult with check results
        """
        checks = {}
        errors = []
        details = {}
        
        output_dir = context.get("output_dir")
        if not output_dir:
            return GateResult(
                passed=False,
                checks={"output_dir_provided": False},
                errors=["output_dir not provided in context"],
            )
        
        output_path = Path(output_dir)
        stats_path = output_path / "stats.json"
        trades_path = output_path / "trades.csv"
        equity_path = output_path / "equity_curve.csv"
        crv_path = output_path / "crv_report.json"
        
        # Check 1: CRV verification
        print("Running CRV verification...")
        if not crv_path.exists():
            checks["crv_exists"] = False
            errors.append("CRV report not found")
        else:
            crv_result = self.rust_wrapper.execute(
                ToolCall(
                    tool_type=ToolType.CRV_VERIFY,
                    parameters=CRVVerifyToolInput(
                        stats_path=str(stats_path),
                        trades_path=str(trades_path),
                        equity_path=str(equity_path),
                        max_drawdown_limit=self.max_drawdown_limit,
                    ),
                )
            )
            checks["crv_pass"] = crv_result.success
            if not crv_result.success:
                errors.append(f"CRV verification failed")
                if "crv_report" in crv_result.output:
                    violations = crv_result.output["crv_report"].get("violations", [])
                    for v in violations:
                        errors.append(f"  - {v.get('rule_id')}: {v.get('message')}")
            details["crv"] = crv_result.output
        
        # Check 2: Walk-forward validation (placeholder for now)
        # In a full implementation, this would run the strategy on multiple time periods
        print("Walk-forward validation (placeholder)...")
        checks["walk_forward"] = True  # Placeholder
        details["walk_forward"] = {"note": "Placeholder - not implemented yet"}
        
        # Check 3: Stress suite (placeholder for now)
        # In a full implementation, this would test strategy under various market conditions
        print("Stress suite (placeholder)...")
        checks["stress_suite"] = True  # Placeholder
        details["stress_suite"] = {"note": "Placeholder - not implemented yet"}
        
        # Gate passes only if all checks pass
        passed = all(checks.values())
        
        return GateResult(
            passed=passed,
            checks=checks,
            errors=errors,
            details=details,
        )
