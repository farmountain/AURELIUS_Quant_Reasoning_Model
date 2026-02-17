"""
Feature flag utilities for primitive API rollout control.

Provides utilities for checking feature flags and handling disabled endpoints.
"""
from fastapi import HTTPException, status
from config import settings


class FeatureFlags:
    """Feature flag checks for primitive endpoints."""
    
    @staticmethod
    def check_primitive_enabled(primitive_name: str):
        """
        Check if a primitive API is enabled via feature flag.
        
        Args:
            primitive_name: Name of primitive (determinism, risk, policy, etc.)
            
        Raises:
            HTTPException 503: If primitive is disabled
        """
        flag_name = f"enable_primitive_{primitive_name}"
        is_enabled = getattr(settings, flag_name, False)
        
        if not is_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Primitive API '{primitive_name}' is currently disabled. "
                       f"Set {flag_name.upper()}=true to enable.",
                headers={"Retry-After": "3600"}
            )
    
    @staticmethod
    def is_primitive_enabled(primitive_name: str) -> bool:
        """
        Check if primitive is enabled without raising exception.
        
        Args:
            primitive_name: Name of primitive
            
        Returns:
            True if enabled, False otherwise
        """
        flag_name = f"enable_primitive_{primitive_name}"
        return getattr(settings, flag_name, False)
    
    @staticmethod
    def get_enabled_primitives() -> list[str]:
        """
        Get list of currently enabled primitives.
        
        Returns:
            List of primitive names that are enabled
        """
        primitives = [
            "determinism", "risk", "policy", "strategy",
            "evidence", "gates", "reflexion", "orchestrator", "readiness"
        ]
        return [p for p in primitives if FeatureFlags.is_primitive_enabled(p)]


def require_primitive_enabled(primitive_name: str):
    """
    Dependency for checking if primitive is enabled.
    
    Usage:
        @router.post("/endpoint", dependencies=[Depends(require_primitive_enabled("determinism"))])
        async def endpoint():
            ...
    """
    def check():
        FeatureFlags.check_primitive_enabled(primitive_name)
    return check
