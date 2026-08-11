import os
from typing import Any

__version__ = "1.0.0"

# The core logic for MemPalace's memory management will live in the /core directory.
# This module serves as the primary entry point for the plugin.

def get_plugin_info() -> dict:
    return {
        "name": "mempalace",
        "version": __version__,
        "description": "Verbatim-first memory system using Wings, Rooms, and Drawers with AAAK compression."
    }

__all__ = ["get_plugin_info"]
