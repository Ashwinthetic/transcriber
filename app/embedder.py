"""Eval-loop adapter exposing this submission's REAL embedding as the
eval suite's app.embedder interface (embed / embed_one / get_model).

Mirrors backend.retrieval.FAISSRetriever's multilingual path exactly:
- same model (KB_EMBEDDING_MODEL or intfloat/multilingual-e5-small)
- same token budget (KB_MAX_SEQ_LENGTH or 384)
- 'query: ' prefix + L2 normalization for queries (encode_query_ml)
- 'passage: ' prefix + L2 normalization for documents (matches the
  Kaggle IVF-PQ index build convention)

Deliberately does NOT load the production knowledge_base/ FAISS indexes:
the eval suite builds its own throwaway index over sampled MSMARCO-XI
candidate passages using THIS module's embed(), then measures whether
this submission's own embeddings rank the gold passage first.
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np


MODEL_NAME = os.getenv("KB_EMBEDDING_MODEL", "intfloat/multilingual-e5-small")

_model = None


def get_model():
    """Loads the submission's real query/passage encoder once."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        print(f"[app.embedder] loading {MODEL_NAME} ...")
        _model = SentenceTransformer(MODEL_NAME)
        try:
            _model.max_seq_length = int(os.getenv("KB_MAX_SEQ_LENGTH", "384"))
        except Exception:
            pass
        print("[app.embedder] model ready.")
    return _model


def embed(texts):
    """Batch-encode documents ('passage: ' prefix, normalized float32)."""
    model = get_model()
    vecs = model.encode(
        [f"passage: {t}" for t in texts],
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return np.array(vecs, dtype="float32")


def embed_one(text):
    """Encode a single query ('query: ' prefix) — same config as the
    production FAISSRetriever.encode_query_ml()."""
    model = get_model()
    vec = model.encode(
        [f"query: {text}"],
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return np.array(vec, dtype="float32")[0]
