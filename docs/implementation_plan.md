# Voice-Based RAG System (Sarvam / ElevenLabs STT + MSMARCO-XI + Latency Benchmark)

Building an end-to-end voice-based Retrieval-Augmented Generation (RAG) system grounded on the `ai4bharat/MSMARCO-XI` dataset with speech-to-text integration (Sarvam & ElevenLabs), multiple chunking strategies, sub-200ms vector retrieval performance, LLM harness with retries and guardrails, automated latency statistics (P50, P70, P100), and a Colab/Kaggle notebook for full 55GB dataset processing.

---

## 🎯 Updated Dataset & Execution Strategy

> [!IMPORTANT]
> **No 55GB Local Download**: 
> 1. **Local System**: Uses a lightweight 1,000-passage curated subset of `ai4bharat/MSMARCO-XI` embedded locally with `faiss-cpu` so startup is instant (<2 seconds), no 55GB download happens on your machine, and local benchmarking consistently runs in sub-200ms.
> 2. **Kaggle / Google Colab Notebook**: We provide `notebooks/rag_msmarco_indexing.ipynb` pre-configured to load the entire 55GB MSMARCO-XI dataset on Kaggle/Colab GPUs, run multi-strategy chunking, build FAISS indices, and export light serialized index files (`msmarco_index.faiss`).

---

## System Architecture Overview

```text
               🎤 Voice Input / Microphone (Web Audio API)
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Sarvam / ElevenLabs  │
                     │        STT API        │
                     └───────────┬───────────┘
                                 │
                                 ▼
                             Text Query
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ Guardrail: Input Safety│
                     │    & Off-Topic Check  │
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Fast Embedding Model │
                     │ (bge-small/all-MiniLM)│
                     └───────────┬───────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  FAISS Vector Index   │
                     │  (Fixed/Sentence/     │
                     │   Semantic/Metadata)  │
                     └───────────┬───────────┘
                                 │
                     Top-K Retrieved Contexts
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │  Guardrail: Context   │
                     │  Groundedness Check   │
                     └───────────┬───────────┘
                                 │
                           Grounded?
                         /           \
                     Yes               No
                     /                   \
        ┌───────────────────┐    ┌────────────────────┐
        │  LLM Harness with │    │ Refusal Fallback:  │
        │ Structured Retries│    │ "Information not   │
        └─────────┬─────────┘    │  found in KB"      │
                  │              └─────────┬──────────┘
                  │                        │
                  └───────────┬────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Latency Metrics Logger│
                  │ (STT, Retrieve, LLM,  │
                  │  P50, P70, P100 stats)│
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Kaggle/Colab Notebook │
                  │  (For 55GB full scale)│
                  └───────────────────────┘
```

---

## User Preferences & Options

1. **STT Provider Preference**: Choice between Sarvam AI (`https://api.sarvam.ai/speech-to-text`) or ElevenLabs STT API.
2. **LLM Generator Provider**: Choice between Groq (ultra-fast <100ms LLM inference), Gemini / OpenAI, or local fast mock generator for sub-200ms benchmarking.
3. **Kaggle / Colab Notebook**: Exportable Jupyter notebook for cloud GPU indexing.

---

## Proposed Changes

### 1. Cloud & Notebook Integration (`notebooks/`)

#### [NEW] [rag_msmarco_indexing.ipynb](file:///c:/transcriber/notebooks/rag_msmarco_indexing.ipynb)
- Google Colab / Kaggle ready Jupyter notebook.
- Downloads full 55GB `ai4bharat/MSMARCO-XI` dataset using GPU acceleration.
- Performs batch chunking across all 4 strategies (Fixed, Sentence, Semantic, Metadata-Aware).
- Generates compressed FAISS vector indices and metadata JSON files to export back to the local app.

---

### 2. Data Processing & Chunking Engine (`data/` & `backend/`)

#### [NEW] [dataset_loader.py](file:///c:/transcriber/data/dataset_loader.py)
- Curates a representative sample passage set (1,000 documents) from MSMARCO-XI locally.
- Provides seamless offline mode without triggering large downloads.

#### [NEW] [chunking.py](file:///c:/transcriber/backend/chunking.py)
- Implements 4 distinct chunking strategies:
  1. **Fixed-Size Chunking** (300 chars, 50 overlap).
  2. **Sentence-Based Chunking** (natural boundaries).
  3. **Semantic Chunking** (cosine distance shifts).
  4. **Metadata-Aware Chunking** (preserves doc_id, source title, question context).

---

### 3. Retrieval Engine (`backend/`)

#### [NEW] [retrieval.py](file:///c:/transcriber/backend/retrieval.py)
- Fast SentenceTransformers embedding (`all-MiniLM-L6-v2` / `bge-small-en-v1.5`).
- In-memory FAISS Vector Store (`IndexFlatIP`).
- Hybrid Search (FAISS + BM25 with Reciprocal Rank Fusion).

---

### 4. Speech-to-Text & LLM Harness (`backend/`)

#### [NEW] [stt_service.py](file:///c:/transcriber/backend/stt_service.py)
- Sarvam AI & ElevenLabs STT integration + mock/fallback audio handler.

#### [NEW] [guardrails.py](file:///c:/transcriber/backend/guardrails.py)
- Safety & Off-Topic Filters + Grounding Similarity Check (refusal on ungrounded queries).

#### [NEW] [llm_harness.py](file:///c:/transcriber/backend/llm_harness.py)
- Retries with exponential backoff, structured JSON response validation, and model switching (Groq / Gemini / OpenAI / Fast Mock).

---

### 5. FastAPI Application & Benchmarking (`backend/` & `benchmarks/`)

#### [NEW] [main.py](file:///c:/transcriber/backend/main.py)
- REST API server with `/api/query`, `/api/stt`, `/api/benchmark`, `/api/strategies`.

#### [NEW] [run_benchmark.py](file:///c:/transcriber/benchmarks/run_benchmark.py)
- Benchmark script measuring sub-200ms latency, P50, P70, and P100 metrics across query suites.

---

### 6. Interactive Web Frontend (`frontend/`)

#### [NEW] [index.html](file:///c:/transcriber/frontend/index.html), [style.css](file:///c:/transcriber/frontend/style.css), [app.js](file:///c:/transcriber/frontend/app.js)
- Modern Glassmorphism dashboard with Voice recorder, Chunk strategy visualizer, Top-K context viewer, Guardrail badges, and Latency statistics cards.

---

### 7. Documentation & Submission Assets (`docs/` & `README.md`)

#### [NEW] [README.md](file:///c:/transcriber/README.md)
#### [NEW] [submission_checklist.md](file:///c:/transcriber/docs/submission_checklist.md)
#### [NEW] [video_script_guidelines.md](file:///c:/transcriber/docs/video_script_guidelines.md)

---

## Verification Plan

### Automated Tests
1. **Local Latency & Chunking Benchmark**:
   ```powershell
   .\backend\.venv\Scripts\python benchmarks/run_benchmark.py
   ```
2. **FastAPI Application Launch**:
   ```powershell
   .\backend\.venv\Scripts\python -m uvicorn backend.main:app --port 8000
   ```

### Manual Verification
- Test UI voice recording & transcription.
- Validate guardrails refutation on off-topic inputs.
- Verify Colab/Kaggle notebook execution flow for full 55GB dataset.

