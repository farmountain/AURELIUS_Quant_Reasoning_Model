"""Finite State Machine for enforcing valid tool call sequences."""

from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from aureus.tools.schemas import ToolType


class State(str, Enum):
    """FSM states representing different stages of the workflow."""
    
    INIT = "init"
    STRATEGY_DESIGN = "strategy_design"
    BACKTEST_READY = "backtest_ready"
    BACKTEST_COMPLETE = "backtest_complete"
    DEV_GATE = "dev_gate"
    DEV_GATE_PASSED = "dev_gate_passed"
    PRODUCT_GATE = "product_gate"
    PRODUCT_GATE_PASSED = "product_gate_passed"
    REFLEXION = "reflexion"
    COMMITTED = "committed"
    ERROR = "error"


@dataclass
class Transition:
    """Represents a valid state transition triggered by a tool call."""
    
    from_state: State
    to_state: State
    tool_type: ToolType
    condition: Optional[str] = None


@dataclass
class FSMState:
    """Current state of the FSM."""
    
    current_state: State = State.INIT
    history: List[State] = field(default_factory=list)
    tool_history: List[ToolType] = field(default_factory=list)
    
    def transition(self, new_state: State, tool_type: ToolType) -> None:
        """Transition to a new state."""
        self.history.append(self.current_state)
        self.tool_history.append(tool_type)
        self.current_state = new_state


class GoalGuardFSM:
    """FSM that enforces valid tool call sequences."""
    
    def __init__(self) -> None:
        """Initialize the FSM with valid transitions."""
        self.state = FSMState()
        self.transitions = self._build_transitions()
    
    def _build_transitions(self) -> Dict[State, Dict[ToolType, State]]:
        """Build the transition table.
        
        Returns:
            Dict mapping (current_state, tool_type) -> next_state
        """
        transitions: Dict[State, Dict[ToolType, State]] = {
            State.INIT: {
                ToolType.GENERATE_STRATEGY: State.STRATEGY_DESIGN,
                ToolType.HIPCORTEX_SEARCH: State.INIT,  # Can search from init
            },
            State.STRATEGY_DESIGN: {
                ToolType.GENERATE_STRATEGY: State.STRATEGY_DESIGN,  # Can iterate
                ToolType.BACKTEST: State.BACKTEST_COMPLETE,
                ToolType.HIPCORTEX_SEARCH: State.STRATEGY_DESIGN,
            },
            State.BACKTEST_READY: {
                ToolType.BACKTEST: State.BACKTEST_COMPLETE,
            },
            State.BACKTEST_COMPLETE: {
                ToolType.RUN_TESTS: State.DEV_GATE,
                ToolType.BACKTEST: State.BACKTEST_COMPLETE,  # Can re-run
            },
            State.DEV_GATE: {
                ToolType.CHECK_DETERMINISM: State.DEV_GATE,
                ToolType.LINT: State.DEV_GATE,
                ToolType.RUN_TESTS: State.DEV_GATE,
                # If all gates pass, external logic moves to DEV_GATE_PASSED
            },
            State.DEV_GATE_PASSED: {
                ToolType.CRV_VERIFY: State.PRODUCT_GATE,
            },
            State.PRODUCT_GATE: {
                ToolType.CRV_VERIFY: State.PRODUCT_GATE,
                # If CRV passes, external logic moves to PRODUCT_GATE_PASSED
            },
            State.PRODUCT_GATE_PASSED: {
                ToolType.HIPCORTEX_COMMIT: State.COMMITTED,
            },
            State.COMMITTED: {
                ToolType.HIPCORTEX_SHOW: State.COMMITTED,
                ToolType.HIPCORTEX_SEARCH: State.COMMITTED,
            },
            State.REFLEXION: {
                # In reflexion, can restart from various points
                ToolType.GENERATE_STRATEGY: State.STRATEGY_DESIGN,
                ToolType.BACKTEST: State.BACKTEST_COMPLETE,
                ToolType.RUN_TESTS: State.DEV_GATE,
            },
            State.ERROR: {
                # From error, must go through reflexion
            },
        }
        return transitions
    
    def can_execute(self, tool_type: ToolType) -> bool:
        """Check if a tool can be executed in the current state.
        
        Args:
            tool_type: The tool to check
            
        Returns:
            True if the tool can be executed, False otherwise
        """
        current_transitions = self.transitions.get(self.state.current_state, {})
        return tool_type in current_transitions
    
    def get_allowed_tools(self) -> Set[ToolType]:
        """Get the set of tools allowed in the current state.
        
        Returns:
            Set of allowed tool types
        """
        return set(self.transitions.get(self.state.current_state, {}).keys())
    
    def transition(self, tool_type: ToolType) -> bool:
        """Attempt to transition based on a tool call.
        
        Args:
            tool_type: The tool being called
            
        Returns:
            True if transition was successful, False if not allowed
        """
        if not self.can_execute(tool_type):
            return False
        
        current_transitions = self.transitions.get(self.state.current_state, {})
        next_state = current_transitions[tool_type]
        
        self.state.transition(next_state, tool_type)
        return True
    
    def force_transition(self, new_state: State) -> None:
        """Force a transition to a new state (for external gate logic).
        
        Args:
            new_state: State to transition to
        """
        # This is used when external logic (like gate runners) determines
        # that a gate has passed or failed
        self.state.history.append(self.state.current_state)
        self.state.current_state = new_state
    
    def get_current_state(self) -> State:
        """Get the current FSM state.
        
        Returns:
            Current state
        """
        return self.state.current_state
    
    def get_state_history(self) -> List[State]:
        """Get the history of states.
        
        Returns:
            List of previous states
        """
        return self.state.history.copy()
    
    def get_tool_history(self) -> List[ToolType]:
        """Get the history of tool calls.
        
        Returns:
            List of previous tool calls
        """
        return self.state.tool_history.copy()
    
    def reset(self) -> None:
        """Reset the FSM to initial state."""
        self.state = FSMState()
    
    def to_reflexion_state(self) -> None:
        """Transition to reflexion state for error recovery."""
        self.force_transition(State.REFLEXION)
    
    def to_error_state(self) -> None:
        """Transition to error state."""
        self.force_transition(State.ERROR)
