# ⚡ Transcriber - Voice-Enabled RAG Studio (<200ms Target Latency)

A high-performance, voice-enabled Retrieval-Augmented Generation (RAG) system built around the **`ai4bharat/MSMARCO-XI`** dataset. Designed for voice RAG requirements: **multi-strategy chunking**, **Sarvam AI STT (`saaras:v3`)**, **FAISS dense vector search (337,018 vectors)**, **Ollama Cloud LLM (`nemotron-3-ultra`)**, **strict dataset grounding guardrails**, and **dual-metric latency analytics (P50, P70, P100)**.

---

## 📊 Performance & Benchmark Metrics

Evaluated across **100+ query topics** across all 4 engineered chunking strategies:

| Metric | Measured Value | Target Threshold | Status |
| :--- | :--- | :--- | :--- |
| **FAISS Vector Retrieval P50** | **11.4 ms** | `< 200 ms` | ✅ COMPLIANT |
| **RAG Core P50 Latency (Embedding + Vector + Guard)** | **16.61 ms** | `< 200 ms` | ✅ COMPLIANT |
| **Voice Stream E2E P50 Latency** | **48.50 ms** | `< 200 ms` | ✅ COMPLIANT |
| **RAG Core Under 200ms Compliance** | **100.0%** | `100%` | ✅ PERFECT |

### Per-Strategy Vector Search Breakdown
- **Fixed-Size Chunking (368 char window)**: P50 = `16.77 ms` | P100 = `27.77 ms`
- **Sentence-Based Chunking (Devanagari-aware)**: P50 = `16.58 ms` | P100 = `26.50 ms`
- **Semantic Chunking (Embedding shifts)**: P50 = `15.95 ms` | P100 = `23.68 ms`
- **Metadata-Aware Chunking (Title & ID prefixed)**: P50 = `16.49 ms` | P100 = `35.95 ms`

---

## 🎯 Key System Architecture & Features

```text
               USER VOICE / TYPED QUESTION
                           ↓
              STT: Sarvam AI saaras:v3
                           ↓
             Query Embedding (e5-small)
                           ↓
        FAISS Search: MSMARCO 337,018 Index
                           ↓
           Retrieved MSMARCO Context Passages
                           ↓
            Grounding Check (Threshold: 0.05)
              /                         \
      Supported                      Not Supported
          ↓                                ↓
Ollama Nemotron 3 Ultra         Refuse: "I couldn't find
          ↓                     sufficient information..."
  Grounded RAG Answer
```

1. **Speech-to-Text (STT) Engine**:
   - **Sarvam AI STT** (`saaras:v3`) with Hindi/Hinglish/English auto-detection.
   - Native Web Speech API streaming transcription for zero-delay speech visualization.

2. **FAISS Dense Vector Index**:
   - Pre-built **337,018 vector index** (`msmarco_xi.faiss`) using `intfloat/multilingual-e5-small`.
   - In-memory BM25 hybrid search fallback with Reciprocal Rank Fusion (RRF).

3. **Grounded LLM Generation Engine**:
   - **Ollama Cloud LLM (`nemotron-3-ultra`)** powered by custom prompt harness.
   - Enforces strict MSMARCO-XI dataset boundary compliance to prevent hallucinations.

4. **Safety & Grounding Guardrails**:
   - Input safety filter (blocks toxic/injection queries).
   - Context similarity thresholding (`GROUNDING_THRESHOLD = 0.05`). Refuses ungrounded queries gracefully.

5. **Modern Emerald Green UI**:
   - Built with **Next.js 16 (Turbopack)**, **Framer Motion**, and **GSAP**.
   - Features Hacker House Goa Emerald Green (`#0A663A`) aesthetics with high-contrast Sun Yellow (`#FDE100`) badges and live latency progress bars.

---

## 🚀 Quick Start Guide

### 1. Installation & Virtual Environment
```powershell
# Navigate to project root
cd c:\transcriber

# Create & activate Python virtual environment
python -m venv backend\.venv
.\backend\.venv\Scripts\activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 2. Environment Setup (`.env`)
Ensure `.env` contains your active API keys:
```env
SARVAM_API_KEY=sk_q088ks1i_rd3BjNC7Mteco4n2jILrP7NO
OLLAMA_API_KEY=c368ff1770154152b6dec820ccee77e5.aJvma-9Qmkqnw7Pd4-CY2WyV
LLM_PROVIDER=ollama
OLLAMA_MODEL=nemotron-3-ultra
```

### 3. Launch Local Application

**Start FastAPI Backend Server (Port 8000)**:
```powershell
.\backend\.venv\Scripts\python -m uvicorn backend.main:app --port 8000 --reload
```

**Start Next.js Frontend Dev Server (Port 3000)**:
```powershell
cd frontend-next
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)** in your browser to start testing.

---

## 📁 Project Directory Structure

```text
c:\transcriber\
├── backend/
│   ├── main.py             # FastAPI Application REST Endpoints
│   ├── retrieval.py        # FAISS Vector Search & BM25 Hybrid Engine
│   ├── stt_service.py      # Sarvam AI STT Service (saaras:v3)
│   ├── guardrails.py       # Input Safety & Grounding Validation
│   ├── llm_harness.py      # Ollama Cloud Nemotron 3 Ultra LLM Harness
│   └── requirements.txt    # Python dependencies
├── frontend-next/
│   ├── app/
│   │   ├── page.tsx        # Next.js 16 Main Dashboard Page
│   │   ├── globals.css     # Emerald Green & High-Contrast Design System
│   │   └── components/     # UI Components (BenchmarkRibbon, ResultsPanel, VectorInspector)
│   └── package.json        # Frontend Dependencies
├── notebooks/              # Kaggle Full-Coverage MSMARCO-XI Indexing Notebooks
├── docs/                   # Documentation & Implementation Reports
└── README.md               # Main Project Documentation
```
