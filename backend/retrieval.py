import os
import sys
import time
from typing import List, Dict, Any, Tuple

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

from data.dataset_loader import load_msmarco_passages
from backend.chunking import ChunkingEngine

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class FAISSRetriever:
    """High-Performance FAISS & BM25 Hybrid Vector Retriever."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"⚡ Initializing SentenceTransformer model: {model_name}...")
        self.model_name = model_name
        self.embedding_model = SentenceTransformer(model_name)
        self.chunking_engine = ChunkingEngine(embedding_model=self.embedding_model)
        
        # Pre-built indexes per strategy
        self.strategy_indexes: Dict[str, Dict[str, Any]] = {}
        # Knowledge base indexes keyed by language code
        self.kb_indexes: Dict[str, Dict[str, Any]] = {}
        self.active_strategy = "sentence_based"
        self._build_indexes()
        self._load_knowledge_bases()

    def _load_knowledge_bases(self):
        """Loads pre-built FAISS IVFPQ indexes from the knowledge_base/ directory."""
        kb_root = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
        if not os.path.exists(kb_root):
            print("ℹ️ No knowledge_base/ directory found, skipping KB loading.")
            return

        target_env = os.getenv("ENABLED_KNOWLEDGE_BASES", "hn").strip()
        target_kbs = [k.strip() for k in target_env.split(",") if k.strip()] if target_env != "all" else None

        for lang_dir in os.listdir(kb_root):
            lang_path = os.path.join(kb_root, lang_dir)
            if not os.path.isdir(lang_path):
                continue

            if target_kbs and lang_dir not in target_kbs:
                continue

            config_path = os.path.join(lang_path, "config.json")
            index_path = os.path.join(lang_path, "faiss_ivfpq.index")

            if not os.path.exists(index_path):
                print(f"⚠️ KB '{lang_dir}': No faiss_ivfpq.index found, skipping.")
                continue

            try:
                import json
                config = {}
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)

                print(f"📦 Loading knowledge base '{lang_dir}' FAISS index from {index_path}...")
                kb_faiss_index = faiss.read_index(index_path)
                lang_code = config.get("language", lang_dir)

                self.kb_indexes[lang_dir] = {
                    "faiss_index": kb_faiss_index,
                    "config": config,
                    "lang_code": lang_code,
                    "total_vectors": kb_faiss_index.ntotal,
                    "dimension": kb_faiss_index.d,
                    "index_type": config.get("index", "IVFPQ"),
                    "embedding_model": config.get("embedding_model", "intfloat/multilingual-e5-small"),
                    "dataset": config.get("dataset", "ai4bharat/MSMARCO-XI"),
                }

                print(
                    f"✅ KB '{lang_dir}' loaded: {kb_faiss_index.ntotal} vectors, "
                    f"dim={kb_faiss_index.d}, lang={lang_code}, "
                    f"model={config.get('embedding_model', 'unknown')}"
                )
            except Exception as e:
                print(f"❌ Failed to load KB '{lang_dir}': {e}")

        if self.kb_indexes:
            print(f"🗂️ Total knowledge bases loaded: {len(self.kb_indexes)} ({', '.join(self.kb_indexes.keys())}) [Filter: {target_env}]")
        else:
            print("ℹ️ No knowledge base indexes were loaded.")

    def _build_indexes(self):
        """Pre-computes and pre-warms vector indexes for all 4 chunking strategies, loading Kaggle index if available."""
        print("⚙️ Building in-memory FAISS & BM25 indexes for MSMARCO dataset...")
        
        # Check if Kaggle pre-built index exists
        kaggle_dir = os.path.join(os.path.dirname(__file__), "..", "data", "results_extracted", "msmarco_xi_artifacts")
        if not os.path.exists(kaggle_dir):
            kaggle_dir = os.path.join(os.path.dirname(__file__), "..", "data", "msmarco_xi_artifacts")
            
        kaggle_faiss = os.path.join(kaggle_dir, "msmarco_xi.faiss")
        kaggle_meta = os.path.join(kaggle_dir, "metadata.jsonl")

        if os.path.exists(kaggle_faiss) and os.path.exists(kaggle_meta):
            try:
                print(f"📦 Loading Kaggle pre-built FAISS index from {kaggle_faiss}...")
                k_faiss_idx = faiss.read_index(kaggle_faiss)
                print(f"✅ Kaggle FAISS loaded: {k_faiss_idx.ntotal} vectors indexed (dim: {k_faiss_idx.d}).")
            except Exception as e:
                print(f"Warning loading Kaggle FAISS index: {e}")

        passages = load_msmarco_passages(sample_size=100)

        strategies = ["fixed_size", "sentence_based", "semantic", "metadata_aware"]
        for st in strategies:
            all_chunks = []
            for doc in passages:
                chunks = self.chunking_engine.chunk_document(
                    text=doc["text"],
                    strategy=st,
                    doc_metadata=doc
                )
                all_chunks.extend(chunks)

            texts = [c["text"] for c in all_chunks]
            if not texts:
                continue

            # Compute dense embeddings
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=64,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            embeddings = np.array(embeddings, dtype="float32")

            # FAISS Index
            dim = embeddings.shape[1]
            faiss_index = faiss.IndexFlatIP(dim)
            faiss_index.add(embeddings)

            # BM25 Index
            tokenized_corpus = [t.lower().split() for t in texts]
            bm25_index = BM25Okapi(tokenized_corpus)

            self.strategy_indexes[st] = {
                "faiss_index": faiss_index,
                "bm25_index": bm25_index,
                "chunks": all_chunks,
                "embeddings": embeddings,
                "total_chunks": len(all_chunks)
            }
            print(f"✅ Strategy '{st}': Indexed {len(all_chunks)} chunks into FAISS & BM25.")

    def retrieve(
        self,
        query: str,
        strategy: str = "sentence_based",
        top_k: int = 3,
        hybrid: bool = True
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Retrieves Top-K relevant chunks with exact millisecond latency benchmarking."""
        t_start = time.perf_counter()
        
        st = strategy if strategy in self.strategy_indexes else "sentence_based"
        idx_data = self.strategy_indexes[st]
        
        faiss_index = idx_data["faiss_index"]
        bm25_index = idx_data["bm25_index"]
        chunks = idx_data["chunks"]

        # Dense Query Embedding
        query_embedding = self.embedding_model.encode(
            [query],
            show_progress_bar=False,
            normalize_embeddings=True
        )
        query_embedding = np.array(query_embedding, dtype="float32")

        # Dense Vector Search
        scores, faiss_indices = faiss_index.search(query_embedding, min(top_k * 3, len(chunks)))
        scores = scores[0]
        faiss_indices = faiss_indices[0]

        if not hybrid:
            results = []
            for i in range(min(top_k, len(faiss_indices))):
                idx = faiss_indices[i]
                if idx < len(chunks):
                    chunk_info = dict(chunks[idx])
                    chunk_info["similarity_score"] = float(scores[i])
                    results.append(chunk_info)
            t_end = time.perf_counter()
            return results, (t_end - t_start) * 1000.0

        # Sparse BM25 Search
        tokenized_query = query.lower().split()
        bm25_scores = bm25_index.get_scores(tokenized_query)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k * 3]

        # Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {}
        k_const = 60

        for rank, idx in enumerate(faiss_indices):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (k_const + rank + 1))

        for rank, idx in enumerate(bm25_top_indices):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + (1.0 / (k_const + rank + 1))

        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, rrf_score in sorted_rrf:
            if idx < len(chunks):
                chunk_info = dict(chunks[idx])
                chunk_info["rrf_score"] = rrf_score
                # Compute raw similarity score
                sim = float(np.dot(query_embedding[0], idx_data["embeddings"][idx]))
                chunk_info["similarity_score"] = sim
                results.append(chunk_info)

        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0
        return results, latency_ms


if __name__ == "__main__":
    retriever = FAISSRetriever()
    results, latency = retriever.retrieve("What are the advantages of solar energy?", strategy="fixed_size", top_k=2)
    print(f"⚡ Retrieval Latency: {latency:.2f} ms")
    for r in results:
        text = r.get('text') or ''
        print(f"- [{r.get('strategy')}] (score: {r.get('similarity_score', 0):.4f}) {text[:100]}...")
