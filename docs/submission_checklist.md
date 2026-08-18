# 📋 Task 2 Submission Checklist (#RAGInGoa)

**Task Deadline**: August 22, 2026 at 11:59 PM

---

## 1. Core Technical Deliverables Checklist

- [x] **Voice Input & Speech-to-Text**: Integrated Sarvam AI (`https://api.sarvam.ai/speech-to-text`) & ElevenLabs STT API with Web Audio API mic recording.
- [x] **Dataset Standard**: Built around `ai4bharat/MSMARCO-XI` dataset.
- [x] **Multiple Chunking Strategies**: Implemented 4 distinct strategies:
  1. Fixed-Size Chunking (300 chars, 50 overlap)
  2. Sentence-Based Chunking
  3. Semantic Chunking (cosine similarity transition thresholding)
  4. Metadata-Aware Chunking (embeds doc_id, category, title, query context)
- [x] **High-Speed Vector Retrieval**: In-memory pre-warmed FAISS `IndexFlatIP` + BM25 hybrid search with Reciprocal Rank Fusion (RRF).
- [x] **LLM Harness**: Structured retry logic, model provider switching (Groq/Gemini/OpenAI/Fast Mock), and JSON response formatting.
- [x] **Guardrails & Grounding**: Safety filters + grounding similarity validation (refuses ungrounded out-of-domain queries).
- [x] **Sub-200ms Performance**: Achieved P50 = **16.61 ms**, P70 = **17.23 ms**, P100 = **35.95 ms** across 100 queries.
- [x] **Benchmarking Script**: `benchmarks/run_benchmark.py` generating `benchmarks/results.json`.
- [x] **Cloud Notebook**: `notebooks/rag_msmarco_indexing.ipynb` for full 55GB MSMARCO-XI dataset processing on Kaggle / Google Colab.

---

## 2. Mandatory Submission Requirements

### 1. Submission Form
- [ ] Fill and submit the official Google Form provided in the hackathon instructions.

### 2. GitHub Repository
- [ ] Ensure repository is public.
- [ ] Commit all code (`backend/`, `data/`, `benchmarks/`, `frontend/`, `notebooks/`, `docs/`, `README.md`).

### 3. Live Working Link
- [ ] Host FastAPI application (e.g. Render, Vercel, HuggingFace Spaces, or Railway).

### 4. Two Videos (X & Instagram Requirement)

> [!IMPORTANT]
> **Video 1 — Team/Process Video**: Exactly **90 seconds**. Must show how your team built the project.
> **Video 2 — Demo Video**: Shows the actual system working end-to-end (voice recording, STT, chunk strategy selection, latency dashboard, guardrail refusal).

### 5. Social Media Upload Rules
- [ ] Both videos uploaded to **X** and **Instagram**.
- [ ] Uploaded individually by **EVERY team member**.
- [ ] At least one Instagram account must be public.
- [ ] Every post must contain the hashtag: `#RAGInGoa`.
