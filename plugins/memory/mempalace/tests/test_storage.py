import pytest
from pathlib import Path
from plugins.memory.mempalace.storage import MemPalaceWrapper

def test_wrapper_initialization():
    """Verify that the wrapper initializes and retrieves the backend correctly."""
    # Use a dummy path; the library should still resolve a default/mocked backend
    db_path = Path("/tmp/test_palace")
    wrapper = MemPalaceWrapper(db_path)
    
    assert wrapper.palace_path == str(db_path)
    backend = wrapper._get_backend()
    assert backend is not None

def test_dummy_methods():
    """Ensure the placeholder methods are present and return expected types."""
    wrapper = MemPalaceWrapper(Path("/tmp/test_palace"))
    assert isinstance(wrapper.create_wing("Work", "Description"), int)
    assert isinstance(wrapper.create_room(1, "Configurator"), int)
    assert isinstance(wrapper.add_drawer(1, "Content"), int)
    assert isinstance(wrapper.search_drawers("query"), list)
