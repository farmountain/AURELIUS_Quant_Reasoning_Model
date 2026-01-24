"""Development gate: tests, determinism, and lint checks."""

from typing import Dict
from aureus.gates.base import Gate, GateResult
from aureus.tools.rust_wrapper import RustEngineWrapper
from aureus.tools.schemas import ToolCall, ToolType


class DevGate(Gate):
    """Development gate that enforces code quality checks."""
    
    def __init__(self, rust_wrapper: RustEngineWrapper):
        """Initialize dev gate.
        
        Args:
            rust_wrapper: Rust engine wrapper for running checks
        """
        self.rust_wrapper = rust_wrapper
    
    def get_name(self) -> str:
        """Get the gate name."""
        return "DevGate"
    
    def run(self, context: Dict[str, any]) -> GateResult:
        """Run development gate checks.
        
        Args:
            context: Must contain 'spec_path' and 'data_path' for determinism check
            
        Returns:
            GateResult with check results
        """
        checks = {}
        errors = []
        details = {}
        
        # Check 1: Run tests
        print("Running tests...")
        test_result = self.rust_wrapper.execute(
            ToolCall(tool_type=ToolType.RUN_TESTS, parameters={})
        )
        checks["tests_pass"] = test_result.success
        if not test_result.success:
            errors.append(f"Tests failed: {test_result.error}")
        details["tests"] = test_result.output
        
        # Check 2: Determinism check
        print("Checking determinism...")
        spec_path = context.get("spec_path")
        data_path = context.get("data_path")
        
        if spec_path and data_path:
            det_result = self.rust_wrapper.execute(
                ToolCall(
                    tool_type=ToolType.CHECK_DETERMINISM,
                    parameters={
                        "spec_path": spec_path,
                        "data_path": data_path,
                        "runs": 3,
                    },
                )
            )
            checks["determinism"] = det_result.success
            if not det_result.success:
                errors.append(f"Determinism check failed: {det_result.error}")
            details["determinism"] = det_result.output
        else:
            checks["determinism"] = False
            errors.append("Missing spec_path or data_path for determinism check")
        
        # Check 3: Lint
        print("Running lint...")
        lint_result = self.rust_wrapper.execute(
            ToolCall(tool_type=ToolType.LINT, parameters={})
        )
        checks["lint"] = lint_result.success
        if not lint_result.success:
            errors.append(f"Lint failed: {lint_result.error}")
        details["lint"] = lint_result.output
        
        # Gate passes only if all checks pass
        passed = all(checks.values())
        
        return GateResult(
            passed=passed,
            checks=checks,
            errors=errors,
            details=details,
        )
