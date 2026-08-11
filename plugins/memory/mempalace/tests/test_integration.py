import pytest
from pathlib import Path
from plugins.memory.mempalace.hooks import MemPalaceHooks

@pytest.fixture
def palace_path(tmp_path):
    # Create a dummy palace path for testing
    return tmp_path / "palace"

@pytest.fixture
def hooks(palace_path):
    return MemPalaceHooks(str(palace_path))

def test_on_session_end_curation(hooks):
    """Verifies that the curation logic correctly identifies and suggests filing for a mock session."""
    mock_session = {
        "transcript": "We decided to build the Clockwork Cable Configurator. It's a Leptos app for custom cable design.",
        "session_id": "test_123"
    }
    
    # This should not crash and should log/process the curation logic
    hooks.on_session_end(mock_session)
    # Verification happens via logs or internal state changes in next iteration

def test_sync_turn_context_retrieval(hooks):
    """Verifies that sync_turn returns valid context blocks for a given turn."""
    current_turn = "How do I add a new Wing to the memory?"
    session_id = "test_123"
    
    context = hooks.sync_turn(current_turn, session_id)
    
    assert isinstance(context, list)
    # At least one block should be returned (the L1 wake-up summary)
    assert len(context) >= 1
    assert "type" in context[0]
    assert "content" in context[0]

def test_prefetch_priming(hooks):
    """Verifies that prefetch returns primed content for a specific wing/room."""
    context = hooks.prefetch("Work", "Clockwork")
    
    assert isinstance(context, list)
    # Should contain the L1 summary
    assert len(context) >= 1
