"""Tests for gate runner blocking on failures."""

import pytest
from unittest.mock import Mock, MagicMock
from aureus.gates.dev_gate import DevGate
from aureus.gates.product_gate import ProductGate
from aureus.tools.rust_wrapper import RustEngineWrapper
from aureus.tools.schemas import ToolResult


def test_dev_gate_blocks_on_test_failure():
    """Test dev gate blocks when tests fail."""
    # Mock rust wrapper
    rust_wrapper = Mock(spec=RustEngineWrapper)
    
    # Mock test failure
    rust_wrapper.execute = Mock(side_effect=[
        ToolResult(success=False, error="Tests failed"),  # Tests
        ToolResult(success=True, output={}),  # Determinism (won't reach)
        ToolResult(success=True, output={}),  # Lint (won't reach)
    ])
    
    dev_gate = DevGate(rust_wrapper)
    
    result = dev_gate.run({
        "spec_path": "test.json",
        "data_path": "test.parquet",
    })
    
    assert not result.passed
    assert "tests_pass" in result.checks
    assert not result.checks["tests_pass"]
    assert len(result.errors) > 0


def test_dev_gate_blocks_on_determinism_failure():
    """Test dev gate blocks when determinism check fails."""
    rust_wrapper = Mock(spec=RustEngineWrapper)
    
    rust_wrapper.execute = Mock(side_effect=[
        ToolResult(success=True, output={}),  # Tests pass
        ToolResult(success=False, error="Not deterministic"),  # Determinism fails
        ToolResult(success=True, output={}),  # Lint
    ])
    
    dev_gate = DevGate(rust_wrapper)
    
    result = dev_gate.run({
        "spec_path": "test.json",
        "data_path": "test.parquet",
    })
    
    assert not result.passed
    assert not result.checks["determinism"]


def test_dev_gate_blocks_on_lint_failure():
    """Test dev gate blocks when lint fails."""
    rust_wrapper = Mock(spec=RustEngineWrapper)
    
    rust_wrapper.execute = Mock(side_effect=[
        ToolResult(success=True, output={}),  # Tests pass
        ToolResult(success=True, output={}),  # Determinism pass
        ToolResult(success=False, error="Lint errors"),  # Lint fails
    ])
    
    dev_gate = DevGate(rust_wrapper)
    
    result = dev_gate.run({
        "spec_path": "test.json",
        "data_path": "test.parquet",
    })
    
    assert not result.passed
    assert not result.checks["lint"]


def test_dev_gate_passes_all_checks():
    """Test dev gate passes when all checks succeed."""
    rust_wrapper = Mock(spec=RustEngineWrapper)
    
    rust_wrapper.execute = Mock(side_effect=[
        ToolResult(success=True, output={}),  # Tests pass
        ToolResult(success=True, output={"deterministic": True}),  # Determinism pass
        ToolResult(success=True, output={}),  # Lint pass
    ])
    
    dev_gate = DevGate(rust_wrapper)
    
    result = dev_gate.run({
        "spec_path": "test.json",
        "data_path": "test.parquet",
    })
    
    assert result.passed
    assert all(result.checks.values())


def test_product_gate_blocks_on_crv_failure():
    """Test product gate blocks when CRV verification fails."""
    rust_wrapper = Mock(spec=RustEngineWrapper)
    
    # Mock CRV failure
    crv_report = {
        "passed": False,
        "violations": [
            {
                "rule_id": "max_drawdown_constraint",
                "severity": "high",
                "message": "Max drawdown exceeds limit",
            }
        ],
    }
    
    rust_wrapper.execute = Mock(return_value=ToolResult(
        success=False,
        output={"crv_report": crv_report},
    ))
    
    product_gate = ProductGate(rust_wrapper, max_drawdown_limit=0.25)
    
    # Create mock output directory with CRV report
    import tempfile
    import json
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create CRV report file
        crv_path = Path(tmpdir) / "crv_report.json"
        with open(crv_path, "w") as f:
            json.dump(crv_report, f)
        
        result = product_gate.run({"output_dir": tmpdir})
        
        assert not result.passed
        assert not result.checks["crv_pass"]
        assert len(result.errors) > 0


def test_product_gate_passes_all_checks():
    """Test product gate passes when all checks succeed."""
    rust_wrapper = Mock(spec=RustEngineWrapper)
    
    crv_report = {
        "passed": True,
        "violations": [],
    }
    
    rust_wrapper.execute = Mock(return_value=ToolResult(
        success=True,
        output={"crv_report": crv_report},
    ))
    
    product_gate = ProductGate(rust_wrapper, max_drawdown_limit=0.25)
    
    import tempfile
    import json
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create CRV report file
        crv_path = Path(tmpdir) / "crv_report.json"
        with open(crv_path, "w") as f:
            json.dump(crv_report, f)
        
        result = product_gate.run({"output_dir": tmpdir})
        
        assert result.passed
        assert result.checks["crv_pass"]


def test_gate_result_string_representation():
    """Test GateResult string representation."""
    from aureus.gates.base import GateResult
    
    result = GateResult(
        passed=True,
        checks={"test1": True, "test2": True},
        errors=[],
    )
    
    assert "PASSED" in str(result)
    assert "2/2" in str(result)
    
    result2 = GateResult(
        passed=False,
        checks={"test1": True, "test2": False},
        errors=["Error in test2"],
    )
    
    assert "FAILED" in str(result2)
    assert "1/2" in str(result2)
