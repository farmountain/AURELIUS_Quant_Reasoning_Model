"""Base gate interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GateResult:
    """Result of a gate check."""
    
    passed: bool
    checks: Dict[str, bool]
    errors: List[str]
    details: Optional[Dict[str, any]] = None
    
    def __str__(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        return f"Gate {status}: {len([v for v in self.checks.values() if v])}/{len(self.checks)} checks passed"


class Gate(ABC):
    """Abstract base class for evidence gates."""
    
    @abstractmethod
    def run(self, context: Dict[str, any]) -> GateResult:
        """Run the gate checks.
        
        Args:
            context: Context information needed for the gate
            
        Returns:
            GateResult with pass/fail status
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the gate name.
        
        Returns:
            Gate name
        """
        pass
