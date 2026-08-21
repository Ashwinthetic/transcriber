import re
import sys
import time
from typing import List, Dict, Any, Tuple

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class RAGGuardrails:
    """Guardrails Engine ensuring Safety, Off-topic Filtering, and Answer Grounding."""

    GROUNDING_THRESHOLD = 0.12
    UNSAFE_PATTERNS = [
        r"\bmalware\b", r"\bhack\b", r"\bexploit\b", r"\bvirus\b", r"\bbomb\b",
        r"\battack\b", r"\bprompt injection\b", r"\bignore previous instructions\b"
    ]

    @classmethod
    def check_input_safety(cls, query: str) -> Tuple[bool, str]:
        """Validates input query against safety and injection filters."""
        query_lower = query.lower()
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, query_lower):
                return False, f"Query triggered safety filter: matched pattern '{pattern}'"
        
        if len(query.strip()) < 2:
            return False, "Query is too short or malformed"
            
        return True, "Input passed safety filter"

    @classmethod
    def check_context_groundedness(
        cls,
        query: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, float, str]:
        """Evaluates whether retrieved passages are relevant enough to ground an answer."""
        if not retrieved_chunks:
            return False, 0.0, "I couldn't find sufficient information in the provided knowledge base to answer that accurately."

        # Extract max similarity score from top chunks
        scores = [c.get("similarity_score", 0.0) for c in retrieved_chunks]
        max_score = max(scores) if scores else 0.0

        if max_score < cls.GROUNDING_THRESHOLD:
            # Check if query is in Hindi
            is_hindi = any('\u0900' <= char <= '\u097F' for char in query) or "kya" in query.lower() or "hai" in query.lower()
            if is_hindi:
                msg = "प्रदान किए गए एमएसमार्को (MSMARCO) नॉलेज बेस में इसका सटीक उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली।"
            else:
                msg = "I couldn't find sufficient information in the provided knowledge base to answer that accurately."
            return False, max_score, msg

        return True, max_score, "Retrieved context meets grounding confidence threshold"


if __name__ == "__main__":
    safe, msg = RAGGuardrails.check_input_safety("What are the advantages of solar energy?")
    print("Safety Check:", safe, msg)

    unsafe, msg = RAGGuardrails.check_input_safety("Write me a malware exploit program")
    print("Unsafe Check:", unsafe, msg)
