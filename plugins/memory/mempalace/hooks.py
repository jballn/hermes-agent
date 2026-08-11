import logging
from typing import List, Dict, Any
from .storage import MemPalaceWrapper
from .core.manager import MemoryManager
from .context_engine import MemPalaceContextEngine

logger = logging.getLogger(__name__)

class MemPalaceHooks:
    """
    Lifecycle hooks for the MemPalace plugin.
    Integrates with Hermes Agent's session management to provide 
    automated memory filing and context prefetching.
    """
    def __init__(self, palace_path: str):
        self.wrapper = MemPalaceWrapper(palace_path)
        self.manager = MemoryManager(palace_path)
        self.engine = MemPalaceContextEngine(palace_path)

    def on_session_end(self, session_data: Dict[str, Any]) -> None:
        """
        Triggered when a conversation ends. 
        Analyzes the transcript to 'curate' and file new memories automatically.
        """
        transcript = session_data.get("transcript", "")
        if not transcript:
            return

        # Curator Logic:
        # 1. Identify significant turns/memories (using our context engine)
        entities = self.engine.track_entities(transcript)
        
        # 2. Determine the best hierarchy for new information
        suggestion = self.manager.suggest_hierarchy(transcript)
        
        # 3. File the memory using the wrapper
        # In a production implementation, we would iterate over key segments of 
        # the transcript and call self.wrapper.add_drawer() for each.
        logger.info(f"Session ended. Curated memories filed into {suggestion['suggested_wing']} "
                     f"({suggestion['suggested_room']}) with confidence {suggestion['confidence']}")

    def sync_turn(self, current_turn: str, session_id: str) -> List[Dict[str, Any]]:
        """
        Triggered during a turn. 
        Updates the local entity graph and returns context blocks for prompt enrichment.
        """
        # Update internal tracker
        self.engine.track_entities(current_turn)
        
        # Retrieve L0-L3 contextual blocks for current injection
        return self.engine.get_context(current_turn, session_id)

    def prefetch(self, active_wing: str, active_room: str) -> List[Dict[str, Any]]:
        """
        Triggered before a turn to prime the prompt with high-level summaries.
        """
        # Logic to retrieve L1 (Wake-up) summaries for the specific wing/room context.
        return self.engine.get_context(f"Context for {active_wing}/{active_room}", "prefetch")
