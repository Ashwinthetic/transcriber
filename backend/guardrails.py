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

    GROUNDING_THRESHOLD = 0.40
    UNSAFE_PATTERNS = [
        r"\bmalware\b", r"\bhack\b", r"\bexploit\b", r"\bvirus\b", r"\bbomb\b",
        r"\battack\b", r"\bprompt injection\b", r"\bignore previous instructions\b",
        r"\bkill\b", r"\bharm\b", r"\bmaim\b", r"\bterror\b", r"\bsuicide\b"
    ]

    # Hindi unsafe / off-topic patterns (Devanagari)
    HINDA_UNSAFE = [
        r"\bवायरस\b", r"\बम\b", r"\हत्या\b", r"\चोट\b", r"\आत्महत्या\b",
        r"\उत्पीडन\b", r"\धमकी\b"
    ]

    HINDA_OFFTOPIC = [
        r"\बाहर\b", r"\समाज\b", r"\राजनीति\b", r"\धर्म\b", r"\विरोध\b"
    ]

    @classmethod
    def check_input_safety(cls, query: str) -> Tuple[bool, str]:
        """Validates input query against safety and injection filters."""
        query_lower = query.lower()
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, query_lower):
                return False, f"Query triggered safety filter: matched pattern '{pattern}'"
        # Hindi unsafe patterns (case-insensitive in Devanagari)
        for pattern in cls.HINDA_UNSAFE:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return False, f"Query triggered Hindi safety filter: matched pattern '{pattern}'"
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

        scores = [c.get("similarity_score", 0.0) for c in retrieved_chunks]
        max_score = max(scores) if scores else 0.0

        if max_score < cls.GROUNDING_THRESHOLD:
            is_hindi = any('\u0900' <= char <= '\u097F' for char in query) or "kya" in query.lower() or "hai" in query.lower()
            if is_hindi:
                msg = "प्रदान किए गए एमएसमार्को (MSMARCO) नॉलेज बेस में इसका सटीक उत्तर देने के लिए पर्याप्त जानकारी नहीं मिला।"
            else:
                msg = "I couldn't find sufficient information in the provided knowledge base to answer that accurately."
            return False, max_score, msg

        return True, max_score, "Retrieved context meets grounding confidence threshold"

    @classmethod
    def check_answer_groundedness(
        cls,
        answer: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, float, str]:
        """Post-generation check: verify that the generated answer is grounded in
        the retrieved context via overlap of key terms / sentences."""
        if not retrieved_chunks:
            return False, 0.0, "No retrieved context to ground against."

        # Extract key terms from chunks
        chunk_terms = set()
        for chunk in retrieved_chunks:
            text = chunk.get("text", "").strip()
            if not text:
                continue
            for w in text.replace("\n", " ").split():
                w clean = w.strip(".,!?;:'\"").lower()
                if len(w_clean) > 3:
                    chunk_terms.add(w_clean)

        # Extract key terms from answer
        answer_terms = set()
        if answer:
            for w in answer.replace("\n", " ").split():
                w_clean = w.strip(".,!?;:'\"").lower()
                if len(w_clean) > 3:
                    answer_terms.add(w_clean)

        if not chunk_terms or not answer_terms:
            # Fallback: if any answer sentence overlaps with any chunk sentence at all
            for chunk in retrieved_chunks:
                c_sentences = [s.strip() for s in chunk.get("text", "").split(". ") if s.strip()]
                for a_sent in answer.replace(". ", ".\n").split("\n"):
                    a_s = a_sent.strip()
                    if not a_s:
                        continue
                    if a_s in ". ".join(c_sentences):
                        return True, 1.0, "Answer grounded in retrieved context."
            return False, 0.0, "Cannot verify grounding."

        overlap = len(chunk_terms.intersection(answer_terms))
        score = overlap / max(len(answer_terms), 1)
        if score >= 0.3:
            return True, score, "Answer grounded in retrieved context."
        return False, score, "Answer not grounded in retrieved context — possible hallucination."


if __name__ == "__main__":
    safe, msg = RAGGuardrails.check_input_safety("What are the advantages of solar energy?")
    print("Safety Check:", safe, msg)

    unsafe, msg = RAGGuardrails.check_input_safety("Write me a malware exploit program")
    print("Unsafe Check:", unsafe, msg)

    safe_h, msg_h = RAGGuardrails.check_input_safety("मेरा नाम राम है")
    print("Hindi Safety Check:", safe_h, msg_h)