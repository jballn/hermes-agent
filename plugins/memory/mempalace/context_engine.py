import os
import json
import logging
import threading
import re
from typing import List, Dict, Optional, Any
from pathlib import Path

# Import the MemPalace library components
try:
    import mempalace
    from mempalace.layers import Layer1
    from mempalace.knowledge_graph import KnowledgeGraph
    from .storage import MemPalaceWrapper
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Mempalace library not found or failed to import components: {e}")
    raise

logger = logging.getLogger(__name__)

class ContextBlock:
    """Represents a structured piece of information for prompt injection."""
    def __init__(self, type: str, source_id: str, content: str, weight: float = 1.0):
        # Types correspond to the 'L0-L3' retrieval strategy
        self.type = type  # 'identity', 'summary', 'relational', 'verbatim'
        self.source_id = source_id
        self.content = content
        self.weight = weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "source": self.source_id,
            "content": self.content,
            "weight": self.weight
        }

class EntityTracker:
    """Handles the identification and tracking of entities within a conversation turn."""
    def __init__(self, palace_path: str):
        # Use the KnowledgeGraph from the library
        self._graph = KnowledgeGraph(db_path=palace_path)
        self._known_entities: set = set()

    def extract_potential_entities(self, text: str) -> List[str]:
        # Attempt to use the library's native entity detector
        try:
            from mempalace.entity_detector import detect_entities
            # The library might expect a list of files or strings; adjust as needed
            # If it fails, we fall back to regex.
            return detect_entities(text)
        except (ImportError, AttributeError):
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            common_false_positives = {"The", "A", "An", "In", "On", "At", "To", "By", "For", "With", "My", "We"}
            return list(set(w for w in words if w not in common_false_positives))

    def resolve_entities(self, text: str) -> Dict[str, List[str]]:
        raw_terms = self.extract_potential_entities(text)
        known, new = [], []
        for term in raw_terms:
            try:
                results = self._graph.query_entity(term)
                if results:
                    known.append(term)
                else:
                    new.append(term)
            except Exception:
                new.append(term)
        return {"known": list(set(known)), "new": list(set(new))}

class MemPalaceContextEngine:
    """
    Implements the Context Engine role for MemPalace.
    Provides Tiered Retrieval (L0-L3) and Knowledge Graph traversal.
    """
    def __init__(self, palace_path: str):
        self.palace_path = palace_path
        # Use our new wrapper to manage the underlying storage/retrieval logic
        self._wrapper = MemPalaceWrapper(Path(palace_path))
        self._tracker = EntityTracker(palace_path)
        self._graph = KnowledgeGraph(db_path=palace_path)

    def track_entities(self, text: str) -> Dict[str, List[str]]:
        """Identifies entities in the current turn and marks them as Known or New."""
        return self._tracker.resolve_entities(text)

    def get_context(self, current_turn_text: str, session_id: str) -> List[Dict[str, Any]]:
        """
        The core Context Engine method.
        Returns a ranked list of context blocks for prompt injection.
        Implementation follows the L0-L3 retrieval strategy:
        L0 (Identity/Profile) - Managed by Hermes primary memory.
        L1 (Wake-up Summary) - High-level goal & pulse summary via Layer1.
        L2 (Relational Context) - Knowledge graph connections for detected entities.
        L3 (Deep Search) - On-demand retrieval (via tools).
        """
        entity_data = self.track_entities(current_turn_text)
        context_blocks = []

        # Layer 1: The Wake-up (High-level overview via our wrapper/library layer)
        try:
            from mempalace.layers import Layer1
            l1 = Layer1(palace_path=self.palace_path)
            context_blocks.append(ContextBlock("summary", "Session_L1", l1.generate(), weight=0.9))
        except Exception as e:
            logger.warning(f"Layer 1 wake-up failed: {e}")

        # Layer 2: Relational Context (Knowledge Graph)
        for entity in entity_data.get("known", []):
            try:
                relationships = self._graph.query_entity(entity)
                for rel in relationships:
                    context_blocks.append(ContextBlock(
                        type="relational",
                        source_id=entity,
                        content=f"Relation: {rel.get('predicate')} -> {rel.get('target')}",
                        weight=0.8
                    ))
            except Exception as e:
                logger.warning(f"Graph query failed for {entity}: {e}")

        return [block.to_dict() for block in context_blocks]

    def get_status(self) -> Dict[str, Any]:
        """Returns health stats of the context engine."""
        try:
            stats = self._graph.stats()
            return {
                "graph_nodes": stats.get("total_entities", 0),
                "graph_edges": stats.get("total_triples", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"error": str(e)}

def register(ctx) -> None:
    from . import MemPalaceProvider
    ctx.register_memory_provider(MemPalaceProvider())
    logger.info("Registered MemPalace as both Memory Provider and Context Engine.")
