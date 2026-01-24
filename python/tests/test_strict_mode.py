"""Tests for strict mode."""

import pytest
from aureus.strict_mode import StrictMode


def test_strict_mode_validates_artifact_id():
    """Test strict mode validates responses with artifact IDs."""
    strict = StrictMode(enabled=True)
    
    # Valid response with artifact ID
    valid_response = "Artifacts:\n" + "a" * 64
    assert strict.validate_response(valid_response)


def test_strict_mode_rejects_no_artifact():
    """Test strict mode rejects responses without artifact IDs."""
    strict = StrictMode(enabled=True)
    
    invalid_response = "Here is some text without an artifact ID"
    assert not strict.validate_response(invalid_response)


def test_strict_mode_rejects_too_much_text():
    """Test strict mode rejects responses with excessive text."""
    strict = StrictMode(enabled=True)
    
    # Too much non-hash text
    invalid_response = (
        "a" * 64 + "\n" +
        "This is a very long explanation that exceeds the character limit for strict mode"
    )
    assert not strict.validate_response(invalid_response)


def test_strict_mode_extract_artifact_ids():
    """Test extracting artifact IDs from text."""
    strict = StrictMode(enabled=True)
    
    text = f"Here are some artifacts: {'a'*64} and {'b'*64}"
    ids = strict.extract_artifact_ids(text)
    
    assert len(ids) == 2
    assert ids[0] == "a" * 64
    assert ids[1] == "b" * 64


def test_strict_mode_format_artifact_response():
    """Test formatting artifact responses."""
    strict = StrictMode(enabled=True)
    
    artifact_ids = ["a" * 64, "b" * 64]
    response = strict.format_artifact_response(artifact_ids, context="Results")
    
    assert "Results" in response
    assert "Artifacts:" in response
    assert "a" * 64 in response
    assert "b" * 64 in response


def test_strict_mode_disabled():
    """Test strict mode when disabled."""
    strict = StrictMode(enabled=False)
    
    # Should accept any response when disabled
    assert strict.validate_response("Any text without artifact IDs")


def test_strict_mode_no_artifacts_response():
    """Test formatting response with no artifacts."""
    strict = StrictMode(enabled=True)
    
    response = strict.format_artifact_response([])
    assert response == "No artifacts"
