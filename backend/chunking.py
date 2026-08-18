import re
import sys
from typing import List, Dict, Any, Optional
import numpy as np

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class ChunkingEngine:
    """Multi-Strategy Chunking Engine for RAG Retrieval Optimizations."""

    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model

    def split_sentences(self, text: str) -> List[str]:
        """Splits text into clean sentence units."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if len(s.strip()) > 0]

    def fixed_size_chunks(
        self,
        text: str,
        chunk_size: int = 250,
        overlap: int = 40,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Strategy 1: Fixed-Size Window Chunking."""
        chunks = []
        start = 0
        text_len = len(text)
        chunk_idx = 0
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_text = text[start:end]
            meta = {
                "strategy": "fixed_size",
                "chunk_id": f"fixed_{doc_metadata.get('doc_id', '0')}_{chunk_idx}" if doc_metadata else f"fixed_{chunk_idx}",
                "text": chunk_text,
                "start_char": start,
                "end_char": end,
                "chunk_len": len(chunk_text),
            }
            if doc_metadata:
                meta.update(doc_metadata)
            chunks.append(meta)
            chunk_idx += 1
            if end >= text_len:
                break
            start += (chunk_size - overlap)
            
        return chunks

    def sentence_based_chunks(
        self,
        text: str,
        max_sentences: int = 2,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Strategy 2: Sentence-Boundary Chunking."""
        sentences = self.split_sentences(text)
        if not sentences:
            sentences = [text]
            
        chunks = []
        chunk_idx = 0
        for i in range(0, len(sentences), max_sentences):
            group = sentences[i:i + max_sentences]
            chunk_text = " ".join(group)
            meta = {
                "strategy": "sentence_based",
                "chunk_id": f"sent_{doc_metadata.get('doc_id', '0')}_{chunk_idx}" if doc_metadata else f"sent_{chunk_idx}",
                "text": chunk_text,
                "sentence_count": len(group),
                "chunk_len": len(chunk_text),
            }
            if doc_metadata:
                meta.update(doc_metadata)
            chunks.append(meta)
            chunk_idx += 1
            
        return chunks

    def semantic_chunks(
        self,
        text: str,
        similarity_threshold: float = 0.65,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Strategy 3: Semantic Similarity Shift Chunking."""
        sentences = self.split_sentences(text)
        if len(sentences) <= 1 or not self.embedding_model:
            return self.sentence_based_chunks(text, max_sentences=2, doc_metadata=doc_metadata)

        embeddings = self.embedding_model.encode(sentences, normalize_embeddings=True)
        chunks = []
        current_group = [sentences[0]]
        chunk_idx = 0

        for i in range(1, len(sentences)):
            sim = np.dot(embeddings[i - 1], embeddings[i])
            if sim >= similarity_threshold:
                current_group.append(sentences[i])
            else:
                chunk_text = " ".join(current_group)
                meta = {
                    "strategy": "semantic",
                    "chunk_id": f"sem_{doc_metadata.get('doc_id', '0')}_{chunk_idx}" if doc_metadata else f"sem_{chunk_idx}",
                    "text": chunk_text,
                    "similarity_last": float(sim),
                    "chunk_len": len(chunk_text),
                }
                if doc_metadata:
                    meta.update(doc_metadata)
                chunks.append(meta)
                chunk_idx += 1
                current_group = [sentences[i]]

        if current_group:
            chunk_text = " ".join(current_group)
            meta = {
                "strategy": "semantic",
                "chunk_id": f"sem_{doc_metadata.get('doc_id', '0')}_{chunk_idx}" if doc_metadata else f"sem_{chunk_idx}",
                "text": chunk_text,
                "chunk_len": len(chunk_text),
            }
            if doc_metadata:
                meta.update(doc_metadata)
            chunks.append(meta)

        return chunks

    def metadata_aware_chunks(
        self,
        text: str,
        doc_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Strategy 4: Metadata-Aware Chunking (Injects structural context)."""
        base_chunks = self.sentence_based_chunks(text, max_sentences=2, doc_metadata=None)
        doc_id = doc_metadata.get("doc_id", "doc_unknown")
        title = doc_metadata.get("title", "MSMARCO Passage")
        category = doc_metadata.get("category", "General")
        query_context = doc_metadata.get("query", "")

        enriched_chunks = []
        for idx, bc in enumerate(base_chunks):
            header = f"[Doc: {title} | Category: {category} | QueryContext: {query_context}] "
            raw = bc["text"]
            formatted_text = f"{header}{raw}"
            
            meta = {
                "strategy": "metadata_aware",
                "chunk_id": f"meta_{doc_id}_{idx}",
                "text": formatted_text,
                "raw_text": raw,
                "header": header,
                "doc_id": doc_id,
                "title": title,
                "category": category,
                "url": doc_metadata.get("url", ""),
                "chunk_len": len(formatted_text),
            }
            enriched_chunks.append(meta)
            
        return enriched_chunks

    def chunk_document(
        self,
        text: str,
        strategy: str = "sentence_based",
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Dispatches chunking according to specified strategy."""
        doc_metadata = doc_metadata or {}
        strategy = strategy.lower()

        if strategy == "fixed_size":
            return self.fixed_size_chunks(text, doc_metadata=doc_metadata)
        elif strategy == "sentence_based":
            return self.sentence_based_chunks(text, doc_metadata=doc_metadata)
        elif strategy == "semantic":
            return self.semantic_chunks(text, doc_metadata=doc_metadata)
        elif strategy == "metadata_aware":
            return self.metadata_aware_chunks(text, doc_metadata=doc_metadata)
        else:
            return self.sentence_based_chunks(text, doc_metadata=doc_metadata)


if __name__ == "__main__":
    engine = ChunkingEngine()
    test_text = "Solar energy is a clean, renewable resource that reduces carbon emissions. Photovoltaic panels convert sunlight into DC electricity. System installation has grown worldwide."
    meta = {"doc_id": "msmarco_001", "title": "Solar Power", "category": "Energy", "query": "Solar benefits"}
    
    print("Fixed Size:", len(engine.chunk_document(test_text, "fixed_size", meta)))
    print("Sentence Based:", len(engine.chunk_document(test_text, "sentence_based", meta)))
    print("Metadata Aware:", engine.chunk_document(test_text, "metadata_aware", meta)[0]["text"])
