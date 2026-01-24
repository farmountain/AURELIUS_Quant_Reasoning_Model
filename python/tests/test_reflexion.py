"""Tests for reflexion loop."""

import pytest
from aureus.reflexion.loop import ReflexionLoop, RepairPlan
from aureus.gates.base import GateResult


def test_reflexion_analyze_test_failure():
    """Test reflexion analyzes test failures correctly."""
    reflexion = ReflexionLoop()
    
    gate_result = GateResult(
        passed=False,
        checks={"tests_pass": False, "determinism": True, "lint": True},
        errors=["Tests failed"],
    )
    
    plan = reflexion.analyze_failure(gate_result)
    
    assert plan.failure_type == "test_failure"
    assert "test" in plan.description.lower()
    assert len(plan.actions) > 0
    assert plan.retry_state == "dev_gate"


def test_reflexion_analyze_determinism_failure():
    """Test reflexion analyzes determinism failures correctly."""
    reflexion = ReflexionLoop()
    
    gate_result = GateResult(
        passed=False,
        checks={"tests_pass": True, "determinism": False, "lint": True},
        errors=["Determinism check failed"],
    )
    
    plan = reflexion.analyze_failure(gate_result)
    
    assert plan.failure_type == "determinism_failure"
    assert "determinism" in plan.description.lower()
    assert len(plan.actions) > 0


def test_reflexion_analyze_crv_failure():
    """Test reflexion analyzes CRV failures correctly."""
    reflexion = ReflexionLoop()
    
    gate_result = GateResult(
        passed=False,
        checks={"crv_pass": False},
        errors=["CRV verification failed"],
    )
    
    plan = reflexion.analyze_failure(gate_result)
    
    assert plan.failure_type == "crv_failure"
    assert "crv" in plan.description.lower()
    assert plan.retry_state == "backtest"


def test_reflexion_should_retry():
    """Test reflexion retry logic."""
    reflexion = ReflexionLoop(max_retries=3)
    
    assert reflexion.should_retry()
    
    reflexion.increment_attempt()
    assert reflexion.should_retry()
    
    reflexion.increment_attempt()
    assert reflexion.should_retry()
    
    reflexion.increment_attempt()
    assert not reflexion.should_retry()


def test_reflexion_reset():
    """Test reflexion reset functionality."""
    reflexion = ReflexionLoop(max_retries=3)
    
    reflexion.increment_attempt()
    reflexion.increment_attempt()
    
    reflexion.reset()
    
    assert reflexion.attempt_count == 0
    assert reflexion.should_retry()


def test_reflexion_generate_failure_summary():
    """Test reflexion generates readable failure summaries."""
    reflexion = ReflexionLoop()
    
    gate_result = GateResult(
        passed=False,
        checks={"tests_pass": True, "determinism": False, "lint": True},
        errors=["Determinism check failed", "Hashes did not match"],
    )
    
    summary = reflexion.generate_failure_summary(gate_result)
    
    assert "Failure Summary" in summary
    assert "✗" in summary  # Failed check marker
    assert "✓" in summary  # Passed check marker
    assert "Determinism check failed" in summary
    assert "Hashes did not match" in summary


def test_repair_plan_dataclass():
    """Test RepairPlan dataclass."""
    plan = RepairPlan(
        failure_type="test_failure",
        description="Tests failed",
        actions=["Fix tests", "Re-run"],
        retry_state="dev_gate",
    )
    
    assert plan.failure_type == "test_failure"
    assert plan.description == "Tests failed"
    assert len(plan.actions) == 2
    assert plan.retry_state == "dev_gate"
