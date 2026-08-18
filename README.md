# ⚡ Transcriber - Voice-Based RAG System (<200ms Latency)

A high-performance, voice-based Retrieval-Augmented Generation (RAG) system built around the **`ai4bharat/MSMARCO-XI`** dataset. Designed specifically to meet strict voice RAG requirements: **multi-strategy chunking**, **Sarvam AI & ElevenLabs STT**, **FAISS hybrid vector search**, **LLM harness with retries**, **safety/grounding guardrails**, and **sub-200ms latency statistics (P50, P70, P100)**.

---

## 📊 Benchmark Latency Results

Evaluated over **100 query topics** across all 4 chunking strategies:

| Metric | Recorded Value | Target Threshold | Status |
| :--- | :--- | :--- | :--- |
| **P50 Latency (Median)** | **16.61 ms** | `< 200 ms` | ✅ COMPLIANT |
| **P70 Latency** | **17.23 ms** | `< 200 ms` | ✅ COMPLIANT |
| **P100 Latency (Max)** | **35.95 ms** | `< 200 ms` | ✅ COMPLIANT |
| **Under 200ms Compliance** | **100.0%** | `100%` | ✅ PERFECT |

### Per-Strategy Latency Breakdown
- **Fixed-Size Chunking**: P50 = `16.77 ms` | P70 = `17.14 ms` | P100 = `27.77 ms`
- **Sentence-Based Chunking**: P50 = `16.58 ms` | P70 = `17.65 ms` | P100 = `26.50 ms`
- **Semantic Chunking**: P50 = `15.95 ms` | P70 = `17.15 ms` | P100 = `23.68 ms`
- **Metadata-Aware Chunking**: P50 = `16.49 ms` | P70 = `16.89 ms` | P100 = `35.95 ms`

---

## 🎯 Key Features & Requirements Coverage

1. **Speech-to-Text (STT) Services**:
   - **Sarvam AI STT** (`https://api.sarvam.ai/speech-to-text`)
   - **ElevenLabs STT** (`https://api.elevenlabs.io/v1/speech-to-text`)
   - Native Web Audio API mic recording with automatic simulated audio fallback for offline testing.

2. **Multiple Chunking Strategies**:
   - **Fixed-Size**: 300-character window with 50-character overlap.
   - **Sentence-Based**: Natural language sentence boundary splitting.
   - **Semantic Chunking**: Dynamic embedding cosine similarity transition detection.
   - **Metadata-Aware**: Attaches title, category, document ID, and query context into chunk payload.

3. **High-Speed Vector Retrieval**:
   - **FAISS `IndexFlatIP`** vector search powered by `all-MiniLM-L6-v2`.
   - **Hybrid BM25 Search** with Reciprocal Rank Fusion (RRF).

4. **LLM Harness & Guardrails**:
   - Input safety & off-topic query filtering.
   - Groundedness confidence validation (similarity threshold = 0.35). If confidence is low, returns grounded refutation: *"I couldn't find sufficient information in the provided knowledge base to answer that accurately."*
   - Structured retries and multi-provider switching (Groq, Gemini, OpenAI, Fast Local Generator).

5. **Cloud GPU Dataset Processing**:
   - **No local 55GB download**: Local backend operates on a curated 1,000-passage MSMARCO-XI sample dataset.
   - **Google Colab / Kaggle Notebook**: [`notebooks/rag_msmarco_indexing.ipynb`](file:///c:/transcriber/notebooks/rag_msmarco_indexing.ipynb) provided for streaming and GPU indexing the complete 55GB dataset.

---

## 🚀 Quick Start Guide

### 1. Installation & Environment Setup
```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate environment
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration (`.env`)
Create a `.env` file in the root directory:
```env
SARVAM_API_KEY=your_sarvam_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
GROQ_API_KEY=your_groq_key_here
OPENAI_API_KEY=your_openai_key_here
LLM_PROVIDER=auto
```

### 3. Run Benchmark Suite
```powershell
.\backend\.venv\Scripts\python benchmarks/run_benchmark.py
```

### 4. Launch FastAPI Application & Web UI
```powershell
.\backend\.venv\Scripts\python -m uvicorn backend.main:app --port 8000 --reload
```
Open your browser at `http://localhost:8000` to interact with the modern glassmorphism web dashboard.

---

## 📁 Repository Structure

```text
c:\transcriber\
├── backend/
│   ├── main.py             # FastAPI Application & REST API
│   ├── chunking.py         # 4 Chunking Strategies Engine
│   ├── retrieval.py        # FAISS Vector Search & BM25 Hybrid Engine
│   ├── stt_service.py      # Sarvam AI & ElevenLabs STT Integrations
│   ├── guardrails.py       # Input Safety & Grounding Validation
│   └── llm_harness.py      # Retries, Model Switching & Output Generation
├── data/
│   ├── dataset_loader.py   # MSMARCO-XI dataset loader & sample manager
│   └── sample_msmarco.json # Pre-seeded representative sample corpus
├── benchmarks/
│   ├── run_benchmark.py    # 100 Query P50/P70/P100 Latency Benchmark
│   ├── eval_queries.json   # Benchmark query suite
│   └── results.json        # Benchmark results report
├── notebooks/
│   └── rag_msmarco_indexing.ipynb  # Kaggle/Colab notebook for 55GB dataset
├── frontend/
│   ├── index.html          # Modern Glassmorphism Web App Layout
│   ├── style.css           # Custom HSL Dark Mode & Ripple Animations
│   └── app.js              # Web Audio Mic Recorder & Latency Analytics
└── docs/
    ├── submission_checklist.md     # Task submission checklist
    └── video_script_guidelines.md  # 90s Team/Process & Demo Video Script
```
