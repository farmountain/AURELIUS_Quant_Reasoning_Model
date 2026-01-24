"""Tests for FSM denying invalid tool sequences."""

import pytest
from aureus.fsm.state_machine import GoalGuardFSM, State
from aureus.tools.schemas import ToolType


def test_fsm_initial_state():
    """Test FSM starts in INIT state."""
    fsm = GoalGuardFSM()
    assert fsm.get_current_state() == State.INIT


def test_fsm_valid_sequence():
    """Test FSM allows valid tool sequence."""
    fsm = GoalGuardFSM()
    
    # Valid sequence: INIT -> STRATEGY_DESIGN -> BACKTEST_COMPLETE
    assert fsm.can_execute(ToolType.GENERATE_STRATEGY)
    assert fsm.transition(ToolType.GENERATE_STRATEGY)
    assert fsm.get_current_state() == State.STRATEGY_DESIGN
    
    assert fsm.can_execute(ToolType.BACKTEST)
    assert fsm.transition(ToolType.BACKTEST)
    assert fsm.get_current_state() == State.BACKTEST_COMPLETE


def test_fsm_denies_invalid_sequence():
    """Test FSM denies invalid tool sequences."""
    fsm = GoalGuardFSM()
    
    # Cannot run backtest from INIT state
    assert not fsm.can_execute(ToolType.BACKTEST)
    assert not fsm.transition(ToolType.BACKTEST)
    assert fsm.get_current_state() == State.INIT
    
    # Cannot commit from INIT state
    assert not fsm.can_execute(ToolType.HIPCORTEX_COMMIT)
    assert not fsm.transition(ToolType.HIPCORTEX_COMMIT)
    assert fsm.get_current_state() == State.INIT


def test_fsm_denies_crv_before_dev_gate():
    """Test FSM denies CRV verification before dev gate passes."""
    fsm = GoalGuardFSM()
    
    # Go to backtest complete
    fsm.force_transition(State.BACKTEST_COMPLETE)
    
    # Cannot run CRV from BACKTEST_COMPLETE
    assert not fsm.can_execute(ToolType.CRV_VERIFY)
    assert not fsm.transition(ToolType.CRV_VERIFY)


def test_fsm_allows_search_from_init():
    """Test FSM allows search from init state."""
    fsm = GoalGuardFSM()
    
    assert fsm.can_execute(ToolType.HIPCORTEX_SEARCH)
    assert fsm.transition(ToolType.HIPCORTEX_SEARCH)
    assert fsm.get_current_state() == State.INIT


def test_fsm_get_allowed_tools():
    """Test getting allowed tools in current state."""
    fsm = GoalGuardFSM()
    
    allowed = fsm.get_allowed_tools()
    assert ToolType.GENERATE_STRATEGY in allowed
    assert ToolType.HIPCORTEX_SEARCH in allowed
    assert ToolType.BACKTEST not in allowed


def test_fsm_state_history():
    """Test FSM tracks state history."""
    fsm = GoalGuardFSM()
    
    fsm.transition(ToolType.GENERATE_STRATEGY)
    fsm.transition(ToolType.BACKTEST)
    
    history = fsm.get_state_history()
    assert State.INIT in history
    assert State.STRATEGY_DESIGN in history


def test_fsm_tool_history():
    """Test FSM tracks tool call history."""
    fsm = GoalGuardFSM()
    
    fsm.transition(ToolType.GENERATE_STRATEGY)
    fsm.transition(ToolType.BACKTEST)
    
    tool_history = fsm.get_tool_history()
    assert ToolType.GENERATE_STRATEGY in tool_history
    assert ToolType.BACKTEST in tool_history


def test_fsm_reset():
    """Test FSM reset functionality."""
    fsm = GoalGuardFSM()
    
    fsm.transition(ToolType.GENERATE_STRATEGY)
    fsm.transition(ToolType.BACKTEST)
    
    fsm.reset()
    
    assert fsm.get_current_state() == State.INIT
    assert len(fsm.get_state_history()) == 0
    assert len(fsm.get_tool_history()) == 0


def test_fsm_reflexion_state():
    """Test FSM reflexion state transitions."""
    fsm = GoalGuardFSM()
    
    fsm.to_reflexion_state()
    assert fsm.get_current_state() == State.REFLEXION
    
    # From reflexion, can restart various operations
    assert fsm.can_execute(ToolType.GENERATE_STRATEGY)
    assert fsm.can_execute(ToolType.BACKTEST)
    assert fsm.can_execute(ToolType.RUN_TESTS)


def test_fsm_complete_workflow():
    """Test complete workflow through FSM."""
    fsm = GoalGuardFSM()
    
    # 1. Generate strategy
    assert fsm.transition(ToolType.GENERATE_STRATEGY)
    assert fsm.get_current_state() == State.STRATEGY_DESIGN
    
    # 2. Run backtest
    assert fsm.transition(ToolType.BACKTEST)
    assert fsm.get_current_state() == State.BACKTEST_COMPLETE
    
    # 3. Run tests (enter dev gate)
    assert fsm.transition(ToolType.RUN_TESTS)
    assert fsm.get_current_state() == State.DEV_GATE
    
    # 4. Check determinism and lint
    assert fsm.transition(ToolType.CHECK_DETERMINISM)
    assert fsm.get_current_state() == State.DEV_GATE
    
    assert fsm.transition(ToolType.LINT)
    assert fsm.get_current_state() == State.DEV_GATE
    
    # 5. Force to dev gate passed (external logic)
    fsm.force_transition(State.DEV_GATE_PASSED)
    
    # 6. Run CRV verification
    assert fsm.transition(ToolType.CRV_VERIFY)
    assert fsm.get_current_state() == State.PRODUCT_GATE
    
    # 7. Force to product gate passed
    fsm.force_transition(State.PRODUCT_GATE_PASSED)
    
    # 8. Commit
    assert fsm.transition(ToolType.HIPCORTEX_COMMIT)
    assert fsm.get_current_state() == State.COMMITTED
