"""Strict mode for enforcing artifact ID-only responses."""

from typing import List, Optional
import re


class StrictMode:
    """Enforces strict mode where responses must cite artifact IDs only."""
    
    def __init__(self, enabled: bool = True):
        """Initialize strict mode.
        
        Args:
            enabled: Whether strict mode is enabled
        """
        self.enabled = enabled
        self.artifact_pattern = re.compile(r"[a-f0-9]{64}")  # SHA-256 hash pattern
    
    def validate_response(self, response: str) -> bool:
        """Validate that a response contains only artifact IDs.
        
        Args:
            response: The response to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not self.enabled:
            return True
        
        # Extract all artifact IDs from response
        artifact_ids = self.extract_artifact_ids(response)
        
        # In strict mode, response should contain at least one artifact ID
        # and minimal additional text
        if not artifact_ids:
            return False
        
        # Check that response is mostly artifact IDs
        # Allow some formatting text but not extensive explanations
        non_hash_text = re.sub(r"[a-f0-9]{64}", "", response)
        non_hash_text = re.sub(r"\s+", " ", non_hash_text).strip()
        
        # Allow up to 50 characters of non-hash text for formatting
        return len(non_hash_text) <= 50
    
    def extract_artifact_ids(self, text: str) -> List[str]:
        """Extract artifact IDs from text.
        
        Args:
            text: Text to extract IDs from
            
        Returns:
            List of artifact IDs
        """
        return self.artifact_pattern.findall(text)
    
    def format_artifact_response(self, artifact_ids: List[str], context: Optional[str] = None) -> str:
        """Format a strict mode response with artifact IDs.
        
        Args:
            artifact_ids: List of artifact IDs to include
            context: Optional brief context
            
        Returns:
            Formatted response string
        """
        if not artifact_ids:
            return "No artifacts"
        
        lines = []
        if context:
            lines.append(context)
        
        lines.append("Artifacts:")
        for artifact_id in artifact_ids:
            lines.append(f"  {artifact_id}")
        
        return "\n".join(lines)
