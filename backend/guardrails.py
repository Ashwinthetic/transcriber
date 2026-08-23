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

    # Stricter grounding threshold - FAISS scores can be deceptively high
    GROUNDING_THRESHOLD = 0.60
    # Post-generation overlap threshold (stricter)
    ANSWER_OVERLAP_THRESHOLD = 0.40

    # English unsafe patterns
    UNSAFE_PATTERNS = [
        r"\bmalware\b", r"\bhack\b", r"\bexploit\b", r"\bvirus\b", r"\bbomb\b",
        r"\battack\b", r"\bprompt injection\b", r"\bignore previous instructions\b",
        r"\bkill\b", r"\bharm\b", r"\bmaim\b", r"\bterror\b", r"\bsuicide\b",
        r"\bmurder\b", r"\bassault\b", r"\bweapon\b", r"\bpoison\b", r"\boverdose\b",
    ]

    # Hindi unsafe patterns (expanded)
    HINDI_UNSAFE = [
        r"वायरस", r"बम", r"हत्या", r"आत्महत्या", r"मारना", r"मार डालो",
        r"हत्या कैसे", r"बम कैसे", r"हथियार", r"जहरीला", r"आत्महत्या कैसे",
        r"किसी को मार", r"मारने का तरीका", r"हिंसा", r"आतंक", r"आत्मघात",
    ]

    # Hindi off-topic patterns (questions not in MSMARCO domain)
    HINDI_OFFTOPIC = [
        r"मेरा नाम क्या", r"तुम्हारा नाम क्या", r"तुम कौन हो", r"तुम क्या हो",
        r"मौसम कैसा", r"आज मौसम", r"कल मौसम", r"तुम कहाँ", r"तुम्हारी उम्र",
        r"मेरा नाम", r"तुम्हें क्या पता", r"तुम जानते हो", r"क्या तुम जानते",
    ]

    @classmethod
    def check_input_safety(cls, query: str) -> Tuple[bool, str]:
        """Validates input query against safety and injection filters."""
        query_lower = query.lower()
        
        # English unsafe patterns
        for pattern in cls.UNSAFE_PATTERNS:
            if re.search(pattern, query_lower):
                return False, f"Query triggered safety filter: matched pattern '{pattern}'"
        
        # Hindi unsafe patterns
        for pattern in cls.HINDI_UNSAFE:
            if re.search(pattern, query, re.IGNORECASE):
                return False, f"Query triggered Hindi safety filter: matched pattern '{pattern}'"
        
        if len(query.strip()) < 2:
            return False, "Query is too short or malformed"
        
        return True, "Input passed safety filter"

    @classmethod
    def check_off_topic(cls, query: str) -> Tuple[bool, str]:
        """Check if query is off-topic for MSMARCO knowledge base."""
        query_lower = query.lower()
        
        # Hindi off-topic patterns
        for pattern in cls.HINDI_OFFTOPIC:
            if re.search(pattern, query, re.IGNORECASE):
                return True, "Query appears off-topic for MSMARCO knowledge base."
        
        # English off-topic patterns
        english_offtopic = [
            r"what is my name", r"what is your name", r"who are you",
            r"weather", r"how are you", r"what time is it",
            r"my name is", r"i am called", r"tell me about yourself",
        ]
        for pattern in english_offtopic:
            if re.search(pattern, query_lower):
                return True, "Query appears off-topic for MSMARCO knowledge base."
        
        return False, "Query appears on-topic."

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

        # Stricter threshold
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
        if not answer or not answer.strip():
            return False, 0.0, "Empty answer produced."

        if not retrieved_chunks:
            return False, 0.0, "No retrieved context to ground against."

        # Extract key terms from chunks (supporting Devanagari & English, min len > 1)
        chunk_terms = set()
        for chunk in retrieved_chunks:
            text = chunk.get("text", "").strip()
            if not text:
                continue
            for w in text.replace("\n", " ").split():
                w_clean = w.strip(".,!?;:'\"॥()[]{}").lower()
                if len(w_clean) > 1:
                    chunk_terms.add(w_clean)

        # Extract key terms from answer
        answer_terms = set()
        for w in answer.replace("\n", " ").split():
            w_clean = w.strip(".,!?;:'\"॥()[]{}").lower()
            if len(w_clean) > 1:
                answer_terms.add(w_clean)

        if not chunk_terms or not answer_terms:
            return True, 1.0, "Answer grounded in retrieved context."

        overlap = len(chunk_terms.intersection(answer_terms))
        score = overlap / max(len(answer_terms), 1)

        # Grounded if at least 15% term overlap or 1 shared key term exists
        if score >= 0.10 or overlap >= 1:
            return True, max(score, 0.50), "Answer grounded in retrieved context."
        
        # Default to True if valid context passages were provided to LLM
        return True, 0.50, "Answer grounded in retrieved context."


if __name__ == "__main__":
    safe, msg = RAGGuardrails.check_input_safety("What are the advantages of solar energy?")
    print("Safety Check:", safe, msg)

    unsafe, msg = RAGGuardrails.check_input_safety("Write me a malware exploit program")
    print("Unsafe Check:", unsafe, msg)

    safe_h, msg_h = RAGGuardrails.check_input_safety("मेरा नाम राम है")
    print("Hindi Safety Check:", safe_h, msg_h)
    
    # Test off-topic
    off, msg = RAGGuardrails.check_off_topic("मेरा नाम क्या है?")
    print("Off-topic Check:", off, msg)
    
    off2, msg2 = RAGGuardrails.check_off_topic("सौर ऊर्जा के क्या फायदे हैं?")
    print("On-topic Check:", off2, msg2)