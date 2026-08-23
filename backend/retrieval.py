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
from backend.record_store import RecordStore, load_record_store

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class FAISSRetriever:
    """High-Performance FAISS & BM25 Hybrid Vector Retriever.

    Primary path: pre-built knowledge_base/<kb>/faiss_ivfpq.index (record-level,
    one vector per MSMARCO-XI source row) + RecordStore parquet shards that map
    FAISS vector ids back to original passages. Index + shards load ONCE at
    startup and stay in RAM; the request path only does embed -> search -> lookup.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.embedding_model = None  # legacy English sample encoder (lazy)
        self.chunking_engine = ChunkingEngine(embedding_model=None)

        # Multilingual embedding model for KB queries (matches Kaggle build config)
        self._ml_model = None
        self._ml_model_name = os.getenv(
            "KB_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"
        )

        # Pre-built indexes per strategy (legacy sample corpus)
        self.strategy_indexes: Dict[str, Dict[str, Any]] = {}
        # Knowledge base indexes keyed by language code
        self.kb_indexes: Dict[str, Dict[str, Any]] = {}
        self.active_strategy = "sentence_based"

        self._load_knowledge_bases()

        if not self.kb_indexes or os.getenv("BUILD_SAMPLE_INDEXES", "0") == "1":
            # Only build the small demo corpus when no real KB is available.
            self.embedding_model = SentenceTransformer(model_name)
            self.chunking_engine = ChunkingEngine(embedding_model=self.embedding_model)
            self._build_indexes()

    # ------------------------------------------------------------ encoding

    def _get_ml_model(self):
        """Loads the multilingual e5 encoder used for both indexing and queries."""
        if self._ml_model is None:
            print(f"⚡ Loading multilingual model: {self._ml_model_name}...")
            self._ml_model = SentenceTransformer(self._ml_model_name)
            # Match the Kaggle indexer token budget exactly
            try:
                self._ml_model.max_seq_length = int(os.getenv("KB_MAX_SEQ_LENGTH", "384"))
            except Exception:
                pass
            print("✅ Multilingual model loaded.")
        return self._ml_model

    def encode_query_ml(self, query: str) -> np.ndarray:
        """Encodes a query with e5-small ('query: ' prefix), L2-normalized — same
        configuration as the Kaggle IVF-PQ index build."""
        ml_model = self._get_ml_model()
        emb = ml_model.encode(
            [f"query: {query}"],
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(emb, dtype="float32")[0]

    def warm_up(self):
        """Runs one dummy encode so the first real request pays no cold-start cost."""
        _ = self.encode_query_ml("warmup")

    # ---------------------------------------------------------- knowledge bases

    def _load_knowledge_bases(self):
        """Loads pre-built FAISS IVFPQ indexes + record stores from knowledge_base/."""
        kb_root = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
        if not os.path.exists(kb_root):
            print("ℹ️ No knowledge_base/ directory found, skipping KB loading.")
            return

        target_env = os.getenv("ENABLED_KNOWLEDGE_BASES", "hn").strip()
        target_kbs = (
            [k.strip() for k in target_env.split(",") if k.strip()]
            if target_env != "all"
            else None
        )

        for lang_dir in sorted(os.listdir(kb_root)):
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
                t0 = time.perf_counter()
                kb_faiss_index = faiss.read_index(index_path)

                nprobe = int(os.getenv("FAISS_NPROBE", "16"))
                try:
                    if hasattr(kb_faiss_index, "nprobe"):
                        kb_faiss_index.nprobe = nprobe
                except Exception:
                    pass

                store = load_record_store(lang_path)
                if not store.available:
                    print(
                        f"⚠️ KB '{lang_dir}': record shards missing "
                        f"(expected {os.path.join(lang_path, 'records')}); "
                        f"text lookup disabled until shards are downloaded from Kaggle."
                    )

                lang_code = config.get("language", lang_dir)
                self.kb_indexes[lang_dir] = {
                    "faiss_index": kb_faiss_index,
                    "record_store": store,
                    "config": config,
                    "lang_code": lang_code,
                    "total_vectors": kb_faiss_index.ntotal,
                    "dimension": kb_faiss_index.d,
                    "index_type": config.get("index", "IVFPQ"),
                    "embedding_model": config.get(
                        "embedding_model", "intfloat/multilingual-e5-small"
                    ),
                    "dataset": config.get("dataset", "ai4bharat/MSMARCO-XI"),
                    "nprobe": nprobe,
                    "load_seconds": round(time.perf_counter() - t0, 2),
                }

                print(
                    f"✅ KB '{lang_dir}' loaded: {kb_faiss_index.ntotal} vectors, "
                    f"dim={kb_faiss_index.d}, lang={lang_code}, nprobe={nprobe}, "
                    f"records={'OK' if store.available else 'MISSING'} "
                    f"({self.kb_indexes[lang_dir]['load_seconds']}s)"
                )
            except Exception as e:
                print(f"❌ Failed to load KB '{lang_dir}': {e}")

        if self.kb_indexes:
            keys = ", ".join(self.kb_indexes.keys())
            print(f"🗂️ Total knowledge bases loaded: {len(self.kb_indexes)} ({keys}) [Filter: {target_env}]")
        else:
            print("ℹ️ No knowledge base indexes were loaded.")

    # ------------------------------------------------------- candidate chunking

    def _chunk_candidates(
        self,
        records: List[Dict[str, Any]],
        strategy: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """Applies candidate-stage multi-strategy chunking to passages of retrieved
        source records (mirrors notebooks/MSMARCO_XI_FULL_COVERAGE_HINDI_KAGGLE.ipynb cell 22).

        Strategies: passage_aware | fixed_size | sentence_based | semantic | metadata_aware
        """
        chunks_out: List[Dict[str, Any]] = []

        for rec in records:
            passages = rec.get("translated_passages") or []
            selected = rec.get("is_selected") or []
            query_type = rec.get("query_type", "")
            target_lang = rec.get("target_lang", "")

            ordered = [
                p for i, p in enumerate(passages)
                if str(p).strip() and (i < len(selected) and selected[i] == 1)
            ] or [p for p in passages if str(p).strip()]
            ordered = ordered[:3]

            for p_idx, passage in enumerate(ordered):
                pieces: List[Tuple[str, str]] = []  # (text, sub_kind)

                if strategy == "passage_aware":
                    pieces.append((passage.strip(), "passage"))
                elif strategy == "fixed_size":
                    size = int(os.getenv("CHUNK_FIXED_SIZE", "500"))
                    overlap = int(os.getenv("CHUNK_FIXED_OVERLAP", "80"))
                    text, start = passage.strip(), 0
                    while start < len(text):
                        end = min(start + size, len(text))
                        piece = text[start:end].strip()
                        if piece:
                            pieces.append((piece, f"fixed_{start}"))
                        if end >= len(text):
                            break
                        start += size - overlap
                elif strategy == "semantic":
                    sentences = [
                        s.strip()
                        for s in __import__("re").split(r"(?<=[.!?।॥])\s+", passage.strip())
                        if s.strip()
                    ]
                    if len(sentences) <= 1:
                        pieces.append((passage.strip(), "semantic"))
                    else:
                        vecs = self._get_ml_model().encode(
                            sentences, normalize_embeddings=True, show_progress_bar=False
                        )
                        thr = float(os.getenv("CHUNK_SEMANTIC_THRESHOLD", "0.58"))
                        cur = [sentences[0]]
                        cur_start = 0
                        for i in range(1, len(sentences)):
                            if float(np.dot(vecs[i - 1], vecs[i])) < thr:
                                pieces.append((" ".join(cur), f"sem_{cur_start}"))
                                cur = [sentences[i]]
                                cur_start = i
                            else:
                                cur.append(sentences[i])
                        if cur:
                            pieces.append((" ".join(cur), f"sem_{cur_start}"))
                else:  # sentence_based (default) | metadata_aware share sentence grouping
                    spc = int(os.getenv("CHUNK_SENTENCES_PER_CHUNK", "3"))
                    sentences = [
                        s.strip()
                        for s in __import__("re").split(r"(?<=[.!?।॥])\s+", passage.strip())
                        if s.strip()
                    ]
                    if not sentences:
                        sentences = [passage.strip()]
                    for gi in range(0, len(sentences), spc):
                        group_text = " ".join(sentences[gi : gi + spc])
                        kind = group_text if strategy != "metadata_aware" else (
                            f"[type={query_type} language={target_lang}] {group_text}"
                        )
                        pieces.append((kind, f"sent_{gi}"))

                for c_i, (c_text, sub_kind) in enumerate(pieces):
                    if not c_text:
                        continue
                    chunks_out.append({
                        "text": c_text,
                        "strategy": strategy,
                        "chunk_id": f"kb_{rec['local_id']}_{p_idx}_{sub_kind}",
                        "doc_id": f"msmarco_xi_{rec['local_id']}",
                        "title": rec.get("query", "")[:120],
                        "category": query_type or "MSMARCO-XI",
                        "similarity_score": rec.get("similarity_score", 0.0),
                        "vector_id": rec["local_id"],
                        "query_id": rec.get("query_id"),
                        "record_query": rec.get("query", ""),
                        "answer": rec.get("answer", ""),
                        "lang": target_lang,
                        "source": "knowledge_base",
                        "index_type": "IVFPQ",
                        "passage_index": p_idx,
                    })
                    if len(chunks_out) >= top_k:
                        return chunks_out

        return chunks_out[:top_k]

    # ------------------------------------------------------------- KB search

    def retrieve_from_kb(
        self,
        query: str,
        lang: str = "hn",
        top_k: int = 5,
        strategy: str = "sentence_based",
    ) -> Tuple[List[Dict[str, Any]], float, Dict[str, float]]:
        """Retrieves Top-K context chunks from a pre-built IVFPQ knowledge base.

        Pipeline: query embedding -> FAISS ANN search -> vector-id -> record
        lookup (parquet shard store) -> candidate-stage chunking.

        Returns (chunks, total_ms, component_ms{embed,search,lookup,chunk}) with
        REAL passage text. If record shards are missing locally, falls back to
        metadata-only results flagged grounded=false so nothing is fabricated.
        """
        t_total = time.perf_counter()
        comp = {"embed": 0.0, "search": 0.0, "lookup": 0.0, "chunk": 0.0}

        if lang not in self.kb_indexes:
            return [], (time.perf_counter() - t_total) * 1000.0, comp

        kb_data = self.kb_indexes[lang]
        kb_faiss = kb_data["faiss_index"]
        store: RecordStore = kb_data["record_store"]

        t0 = time.perf_counter()
        q_vec = self.encode_query_ml(query)
        q_vec = np.expand_dims(q_vec, axis=0)
        comp["embed"] = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        search_k = max(top_k, int(os.getenv("KB_CANDIDATE_RECORDS", "8")))
        search_k = min(search_k, int(kb_faiss.ntotal))
        scores, ids = kb_faiss.search(q_vec, search_k)
        comp["search"] = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        candidate_records: List[Dict[str, Any]] = []
        for score, vec_id in zip(scores[0], ids[0]):
            vid = int(vec_id)
            if vid < 0:
                continue
            rec = store.get(vid)
            if rec is None:
                continue
            rec["similarity_score"] = float(score)
            candidate_records.append(rec)
        comp["lookup"] = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        chunks = self._chunk_candidates(candidate_records, strategy, top_k)
        comp["chunk"] = (time.perf_counter() - t0) * 1000.0

        if not chunks and candidate_records and not store.available:
            # Shards missing entirely — surface honest empty result, never fake text.
            return [], (time.perf_counter() - t_total) * 1000.0, comp

        total_ms = (time.perf_counter() - t_total) * 1000.0
        return chunks, total_ms, comp

    # ------------------------------------------------- legacy sample retrieval

    def _build_indexes(self):
        """Pre-computes demo FAISS/BM25 indexes over the 100-passage English sample."""
        print("⚙️ Building in-memory FAISS & BM25 indexes for MSMARCO sample dataset...")

        kaggle_dir = os.path.join(
            os.path.dirname(__file__), "..", "data", "results_extracted", "msmarco_xi_artifacts"
        )
        if not os.path.exists(kaggle_dir):
            kaggle_dir = os.path.join(os.path.dirname(__file__), "..", "data", "msmarco_xi_artifacts")

        kaggle_faiss = os.path.join(kaggle_dir, "msmarco_xi.faiss")

        if os.path.exists(kaggle_faiss):
            try:
                print(f"📦 (info) Larger Kaggle artifact present at {kaggle_faiss} (not loaded; KB indexes take priority)")
            except Exception:
                pass

        passages = load_msmarco_passages(sample_size=100)

        strategies = ["fixed_size", "sentence_based", "semantic", "metadata_aware"]
        for st in strategies:
            all_chunks = []
            for doc in passages:
                chunks = self.chunking_engine.chunk_document(
                    text=doc["text"], strategy=st, doc_metadata=doc
                )
                all_chunks.extend(chunks)

            texts = [c["text"] for c in all_chunks]
            if not texts:
                continue

            embeddings = self.embedding_model.encode(
                texts, batch_size=64, show_progress_bar=False, normalize_embeddings=True
            )
            embeddings = np.array(embeddings, dtype="float32")

            dim = embeddings.shape[1]
            faiss_index = faiss.IndexFlatIP(dim)
            faiss_index.add(embeddings)

            tokenized_corpus = [t.lower().split() for t in texts]
            bm25_index = BM25Okapi(tokenized_corpus)

            self.strategy_indexes[st] = {
                "faiss_index": faiss_index,
                "bm25_index": bm25_index,
                "chunks": all_chunks,
                "embeddings": embeddings,
                "total_chunks": len(all_chunks),
            }
            print(f"✅ Strategy '{st}': Indexed {len(all_chunks)} chunks into FAISS & BM25.")

    def retrieve_with_components(
        self,
        query: str,
        strategy: str = "sentence_based",
        top_k: int = 3,
        lang: str = "",
    ) -> Tuple[List[Dict[str, Any]], float, Dict[str, float]]:
        """Retrieves with per-component latency breakdown.
        
        Returns (chunks, total_latency_ms, component_latencies_dict).
        Component dict keys: embed, search, lookup, chunk (for KB path)
        or empty dict for legacy path.
        """
        if lang and lang in self.kb_indexes:
            return self.retrieve_from_kb(
                query, lang=lang, top_k=top_k, strategy=strategy
            )
        
        # Legacy sample path - no component breakdown available
        t_start = time.perf_counter()
        chunks, lat = self.retrieve(query, strategy=strategy, top_k=top_k, lang=lang)
        return chunks, lat, {}

    def retrieve(
        self,
        query: str,
        strategy: str = "sentence_based",
        top_k: int = 3,
        hybrid: bool = True,
        lang: str = "",
    ):
        """Top-K retrieval. Routes to KB path when lang matches a loaded KB.

        Returns (chunks, latency_ms) — for KB mode also attaches `components`
        dict on the returned tuple via attribute for backward compatibility.
        """
        if lang and lang in self.kb_indexes:
            chunks, lat, comp = self.retrieve_from_kb(
                query, lang=lang, top_k=top_k, strategy=strategy
            )
            self.last_components = comp
            return chunks, lat

        t_start = time.perf_counter()
        if not self.strategy_indexes:
            self.last_components = {}
            return [], (time.perf_counter() - t_start) * 1000.0

        st = strategy if strategy in self.strategy_indexes else "sentence_based"
        idx_data = self.strategy_indexes[st]

        faiss_index = idx_data["faiss_index"]
        bm25_index = idx_data["bm25_index"]
        chunks = idx_data["chunks"]

        query_embedding = self.embedding_model.encode(
            [query], show_progress_bar=False, normalize_embeddings=True
        )
        query_embedding = np.array(query_embedding, dtype="float32")

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
            self.last_components = {}
            return results, (time.perf_counter() - t_start) * 1000.0

        tokenized_query = query.lower().split()
        bm25_scores = bm25_index.get_scores(tokenized_query)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][: top_k * 3]

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
                sim = float(np.dot(query_embedding[0], idx_data["embeddings"][idx]))
                chunk_info["similarity_score"] = sim
                results.append(chunk_info)

        self.last_components = {}
        return results, (time.perf_counter() - t_start) * 1000.0


if __name__ == "__main__":
    retriever = FAISSRetriever()
    if retriever.kb_indexes:
        chunks, lat, comp = retriever.retrieve_from_kb(
            "सौर ऊर्जा के क्या फायदे हैं?", lang="hn", top_k=3
        )
        print(f"⚡ KB Retrieval Latency: {lat:.2f} ms | components: { {k: round(v,2) for k,v in comp.items()} }")
        for r in chunks:
            print(f"- [{r['strategy']}] (score: {r['similarity_score']:.4f}) {r['text'][:120]}...")
    else:
        results, latency = retriever.retrieve("What are the advantages of solar energy?", strategy="fixed_size", top_k=2)
        print(f"⚡ Sample Retrieval Latency: {latency:.2f} ms")
