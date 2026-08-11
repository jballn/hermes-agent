import re
from typing import List, Dict, Optional

# === EMOTION CODES (universal) ===
EMOTION_CODES = {
    "vulnerability": "vul",
    "joy": "joy",
    "fear": "fear",
    "trust": "trust",
    "grief": "grief",
    "wonder": "wonder",
    "rage": "rage",
    "love": "love",
    "hope": "hope",
    "despair": "despair",
    "peace": "peace",
    "relief": "relief",
    "humor": "humor",
    "tenderness": "tender",
    "raw_honesty": "raw",
    "self_doubt": "doubt",
    "anxiety": "anx",
    "exhaustion": "exhaust",
    "conviction": "convict",
    "quiet_passion": "passion",
}

# Keywords that signal emotions in plain text
_EMOTION_SIGNALS = {
    "decided": "determ",
    "prefer": "convict",
    "worried": "anx",
    "excited": "excite",
    "frustrated": "frust",
    "confused": "confuse",
    "love": "love",
    "hate": "rage",
    "hope": "hope",
    "fear": "fear",
    "trust": "trust",
    "happy": "joy",
    "sad": "grief",
    "surprised": "surprise",
    "grateful": "grat",
    "curious": "curious",
    "wonder": "wonder",
    "anxious": "anx",
    "relieved": "relief",
    "satisfaction": "satis",
    "disappointment": "grief",
    "concern": "anx",
}

# Keywords that signal flags
_FLAG_SIGNALS = {
    "decided": "DECISION",
    "chose": "DECISION",
    "switched": "DECISION",
    "migrated": "DECISION",
    "replaced": "DECISION",
    "instead of": "DECISION",
    "because": "DECISION",
    "founded": "ORIGIN",
    "created": "ORIGIN",
    "started": "ORIGIN",
    "born": "ORIGIN",
    "launched": "ORIGIN",
    "first time": "ORIGIN",
    "core": "CORE",
    "fundamental": "CORE",
    "essential": "CORE",
    "principle": "CORE",
    "belief": "CORE",
    "always": "CORE",
    "never forget": "CORE",
    "turning point": "PIVOT",
    "changed everything": "PIVOT",
    "realized": "PIVOT",
    "breakthrough": "PIVOT",
    "epiphany": "PIVOT",
    "api": "TECHNICAL",
    "database": "TECHNICAL",
    "architecture": "TECHNICAL",
    "deploy": "TECHNICAL",
    "infrastructure": "TECHNICAL",
    "algorithm": "TECHNICAL",
    "framework": "TECHNICAL",
    "server": "TECHNICAL",
    "config": "TECHNICAL",
}

class Dialect:
    """
    AAAK Dialect -- Compressed Symbolic Summary Format.
    Extracts entities, topics, key sentences, emotions, and flags 
    into a compact structured representation for LLM-native recall.
    """

    def __init__(self):
        pass

    def encode_entity(self, name: str) -> str:
        """Abbreviate personal/project names to first 3 chars uppercase."""
        return name[:3].upper()

    def _extract_emotions(self, text: str) -> str:
        codes = []
        for word, code in _EMOTION_SIGNALS.items():
            if word in text.lower():
                if code not in codes:
                    codes.append(code)
        return "+".join(codes[:3])

    def _extract_flags(self, text: str) -> str:
        found_flags = set()
        for word, flag in _FLAG_SIGNALS.items():
            if word in text.lower():
                found_flags.add(flag)
        return "+".join(sorted(list(found_flags)))

    def compress(self, text: str) -> str:
        """
        Heuristic compression pipeline:
        1. Entity Detection & Encoding
        2. Topic Extraction (Simplified as keywords for now)
        3. Emotional Tagging
        4. Flag Assignment
        """
        # This is a simplified version of the MemPalace dialect.compress 
        # designed to work within our plugin's scope without full NLP.
        
        # Example: "We decided to use Clerk for auth because it was cheaper."
        # Result: DECISION: use_clerk|auth(cheaper)|****
        
        # Placeholder logic for the compression step:
        summary = f"RECAP: {text[:100]}..." # Fallback
        
        # Logic to find a primary action or decision (Simplified)
        if "decided" in text.lower() or "chose" in text.lower():
            summary = f"DECISION: {text[:50]}... |{self._extract_emotions(text)}|{self._extract_flags(text)}"
        elif "created" in text.lower() or "founded" in text.lower():
            summary = f"ORIGIN: {text[:50]}... |{self._extract_emotions(text)}|{self._extract_flags(text)}"
            
        return summary

# Helper for storage integration
def auto_compress_content(content: str) -> tuple[str, float, str]:
    """Returns (aaak_summary, emotional_weight, flags)."""
    dialect = Dialect()
    summary = dialect.compress(content)
    
    # Simple weight calculation based on presence of critical flags/emotions
    weight = 0.5
    if "DECISION" in summary or "ORIGIN" in summary:
        weight = 0.9
    
    flags = summary.split("|")[-1] if "|" in summary else ""
    return summary, weight, flags
