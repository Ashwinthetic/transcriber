# Transcriber AI - Implementation Progress

## Project Overview
Voice-enabled RAG system for Hindi (MSMARCO-XI) with sub-200ms latency target.

## Architecture (Implemented)

```
Voice → Sarvam STT → Query Embedding (e5-small) → FAISS IVF-PQ → Record Store Lookup → Candidate Chunking → Ollama LLM → Guardrails → Answer
```

## Completed Components

### 1. FAISS Knowledge Base (Hindi) ✅
- **Index**: `knowledge_base/hn/faiss_ivfpq.index`
- **Vectors**: 778,638
- **Dimensions**: 384
- **Index Type**: IVF-PQ (nlist=4096, PQ=48x8)
- **Embedding Model**: intfloat/multilingual-e5-small
- **Record Store**: Available (records=OK)

### 2. Backend (FastAPI) ✅
- **File**: `backend/main.py`
- **Endpoints**:
  - `POST /api/query` - Main RAG pipeline
  - `GET /api/knowledge-bases` - KB status
  - `GET /api/strategies` - Chunking strategies
  - `GET /api/benchmark` - Benchmark results
  - `GET /` - Frontend

### 3. FAISS Retrieval (`backend/retrieval.py`) ✅
- IVF-PQ search with nprobe=16
- Memory-mapped parquet record store lookup
- Candidate-stage chunking (5 strategies):
  - passage_aware, fixed_size, sentence_based, semantic, metadata_aware
- Per-component latency tracking

### 4. Record Store (`backend/record_store.py`) ✅
- Memory-mapped parquet shard access
- Vector ID → {translated_passages, is_selected, query, answer, metadata}
- Graceful degradation when shards missing

### 5. LLM Harness (`backend/llm_harness.py`) ✅
- Primary: Ollama local (qwen2.5:0.5b)
- Fallback: Groq → fast_grounded
- Retries, timeouts, bounded cache
- Structured output

### 6. Guardrails (`backend/guardrails.py`) ✅
- Input safety (English + Hindi patterns)
- Off-topic detection (Hindi + English)
- Context groundedness (threshold: 0.60)
- Post-generation answer grounding (overlap threshold: 0.40)

### 7. STT Service (`backend/stt_service.py`) ✅
- Sarvam AI (saaras:v3) + ElevenLabs
- Simulated mode for testing
- No hardcoded API keys

### 8. Chunking Engine (`backend/chunking.py`) ✅
- 5 strategies implemented
- Devanagari-aware sentence splitting

### 9. STT Service ✅
- Sarvam AI + ElevenLabs integration
- Simulated mode for benchmarks

### 9. Pipeline Benchmark (`benchmarks/run_pipeline_benchmark.py`) ✅
- 20+ query test with real Ollama
- Per-component latency tracking
- P50/P70/P100/avg/min/max reporting

## Benchmark Results (20 queries, qwen2.5:0.5b on CPU)

| Component | P50 | P70 | P100 |
|---|---|---|---|
| STT (simulated) | 0.0ms | 0.0ms | 0.0ms |
| Embedding | 75.5ms | 92.9ms | 11,091ms* |
| FAISS Search | 1.7ms | 2.2ms | 4.4ms |
| Record Lookup | 107.9ms | 124.2ms | 800.8ms |
| Chunking | 0.17ms | 0.19ms | 0.46ms |
| Guardrails | 0.25ms | 0.29ms | 1.38ms |
| **LLM (Ollama)** | **8,779ms** | **9,753ms** | **19,841ms** |
| **Total** | **9,149ms** | **9,981ms** | **31,006ms** |

**Under 200ms: 0%** - Ollama is the bottleneck (~9s on CPU)

### Guardrail Test Results (12 queries)
- Factual queries: 4/4 PASS ✅
- Off-topic: 1/3 PASS ❌ (2 hallucinated)
- Unsafe: 2/3 PASS ❌ (1 hallucinated)
- Unsupported: 0/2 PASS ❌ (both hallucinated)

## Known Issues

### 1. Ollama Latency (CRITICAL)
- **Current**: ~9s P50 on CPU (qwen2.5:0.5b)
- **Target**: <200ms total
- **Solutions needed**:
  - GPU acceleration (CUDA)
  - Smaller model (0.5B params minimum)
  - Quantization (4-bit/INT8)
  - Batched inference
  - Consider dedicated LLM server (vLLM, TGI)

### 2. Guardrails Need Tuning
- Off-topic detection: 2/3 false negatives (hallucinated answers)
- Unsupported queries: Both hallucinated instead of refusing
- Need: Higher grounding threshold, better semantic off-topic detection

### 3. Windows Server Binding Issue
- uvicorn/hypercorn claim to start but don't bind to port on Windows
- Workaround: Run via `python -c "import uvicorn; uvicorn.run(...)"` 
- Production: Use Linux container or Windows Service

### 4. Record Shards
- Currently available (records=OK)
- Source: Kaggle notebook outputs (msmarco_xi_full/hi/records/)
- ~2GB for Hindi, not in repo

## Remaining Work

### Phase 1: Fix Ollama Latency (Priority 1)
- [ ] Test with GPU (if available)
- [ ] Try smaller model (0.5B params)
- [ ] Try 4-bit quantization
- [ ] Try vLLM/TGI for batched inference
- [ ] Benchmark with <200ms target

### Phase 2: Improve Guardrails
- [ ] Increase GROUNDING_THRESHOLD to 0.65-0.70
- [ ] Improve off-topic semantic detection
- [ ] Add query classification step
- [ ] Better Hindi off-topic patterns

### Phase 3: Public Access & Frontend
- [ ] ngrok/cloudflared tunnel setup
- [ ] Frontend integration testing
- [ ] CORS configuration for production

### Phase 4: Production Deployment
- [ ] Linux container (Docker)
- [ ] Supabase for app data (sessions, history)
- [ ] Environment variable management
- [ ] Monitoring/alerting

## Files Modified/Created

### Core Backend
- `backend/main.py` - FastAPI app, pipeline orchestration
- `backend/retrieval.py` - FAISS + RecordStore retrieval
- `backend/record_store.py` - Parquet record store
- `backend/llm_harness.py` - LLM orchestration
- `backend/guardrails.py` - Safety, off-topic, grounding
- `backend/stt_service.py` - STT integration
- `backend/chunking.py` - 5 chunking strategies
- `backend/__init__.py` - Package init

### Benchmarks
- `benchmarks/run_pipeline_benchmark.py` - Full pipeline benchmark

### Frontend
- `frontend/index.html` - Updated lang codes (hn, gn, bn, mr, or, as)
- `frontend/app.js` - Already compatible

### Deleted (pgvector experiment)
- `backend/pg_retrieval.py`
- `scripts/ingest_kb_to_pg.py`
- `scripts/test_pg_latency.py`
- `scripts/db_healthcheck.py`
- `scripts/setup_db_url.py`
- `docs/pgvector_teaching_book.md`
- `scripts/` directory

### Config
- `requirements.txt` - Removed psycopg, pgvector
- `.env` - OLLAMA_MODEL=qwen2.5:0.5b

## How to Run

### Start Backend
```bash
cd C:\transcriber
C:\transcriber\backend\.venv\Scripts\python.exe -c "
import uvicorn, sys
sys.path.insert(0, r'C:\transcriber\backend')
from backend.main import app
uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
"
```

### Test API
```bash
python -c "
import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')
data = json.dumps({'query': 'सौर ऊर्जा के क्या फायदे हैं?', 'lang': 'hn', 'strategy': 'sentence_based'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/query', data=data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=60) as r:
    print(json.dumps(json.loads(r.read().decode()), indent=2, ensure_ascii=False))
"
```

### Run Benchmark
```bash
C:\transcriber\backend\.venv\Scripts\python.exe C:\transcriber\benchmarks\run_pipeline_benchmark.py --lang hn --queries 20 --live-llm
```

### View Frontend
```
http://127.0.0.1:8000/
```

## Next Immediate Steps

1. **Fix Ollama latency** - This is the single blocker for <200ms target
2. **Run 100-query benchmark** once latency is fixed
3. **Set up ngrok/cloudflared** for public HTTPS
4. **Frontend integration testing**
5. **Document final results**

---

*Last Updated: 2026-08-23*
*Status: Backend complete, Ollama latency is primary blocker*