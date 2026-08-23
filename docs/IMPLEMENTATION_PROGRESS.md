# Implementation Progress — Hindi Voice RAG Pipeline

Status document. Updated continuously as work happens.

Legend: MEASURED (real numbers with date/config) · ESTIMATE — NOT BENCHMARKED · NOT TESTED YET

---

## 1. Project goal

Deployable voice RAG: Sarvam STT → multilingual-e5-small → existing FAISS
IVF-PQ retrieval → real Hindi passage lookup → candidate-stage chunking →
real Ollama generation → grounding/guardrails → answer. Hindi first; other
languages and Supabase explicitly deferred.

## 2. Final architecture

FAISS stays the vector engine. No pgvector, no Supabase vectors, no per-query
HF calls on the normal path.

```
Voice → Sarvam STT (saaras:v3)            [text path tested first]
      → intfloat/multilingual-e5-small ("query: " prefix, normalized)
      → knowledge_base/hn/faiss_ivfpq.index  (IVF-PQ nlist=4096 PQ48x8)
      → top-k vector ids (= local_id = row ordinal in train/hintrain.parquet)
      → compact passage store (passages.parquet, memory-mapped row groups)
      → candidate-stage chunking (sentence_based default)
      → Ollama local daemon, model OLLAMA_MODEL=llama3.2:1b from .env
      → input / context / post-generation guardrails
      → answer + per-component latencies
```

## 3. Existing FAISS knowledge base (untouched)

- `knowledge_base/hn/faiss_ivfpq.index` — 778,638 × 384-dim, IVF-PQ,
  nlist=4096, PQ 48x8, e5-small. Not rebuilt/modified.
- bn/gn/mr/ka/or indexes present and untouched.

## 4. Hindi dataset/index details (MEASURED 2026-08-23)

- Source: `ai4bharat/MSMARCO-XI`, file `train/hintrain.parquet`
- Remote size 3,719,813,179 B (3.72 GB); rows 778,638; ONE parquet row group
  (no remote row pruning possible ⇒ remote per-row lookups structurally slow)
- Column sizes (footer probe): Translated_passages 2.198 GB compressed /
  6.757 GB uncompressed; English_passages 1.389 GB compressed (dropped)
- Downloaded once to `data/source/hintrain.parquet` for one-time preparation

## 5. FAISS ID → passage mapping (verified)

- vector_id == local_id == row ordinal (config.json:
  source_rows==records_indexed==778638, all_records=true)
- Old Kaggle metadata.jsonl does NOT match this index (337,018 ≠ 778,638)
- Chain verified with real text: id 389319 → "उच्चतम मूल्यवर्ग वाली अमेरिकी मुद्रा" + 10 Hindi passages

## 6. Passage store — MEASURED (built 2026-08-23 20:59)

- File: `knowledge_base/hn/passage_store/passages.parquet`
- **1,422.5 MB** zstd parquet, 3,075 row groups × 256 rows, sha-batch-verified
- Contains ALL of: 778,638 rows · **7,769,498 real Hindi passages**
  (avg 9.98/row, avg 3,397 chars/row) · 513,004 is_selected gold passages
- Columns kept: local_id, query, answer, query_type, target_lang,
  translated_passages, is_selected. Dropped: english_passages, Eng_*, meta
- Lookup latency (single, random ids, cold-ish): P50 5.69 ms / P90 8.69 ms /
  P100 17.95 ms (n=300); warm ≈ 6.5 ms
- Store open time at startup: ~0.31–0.38 s (footer + group index only)
- Builder: `backend/build_passage_store.py` (reproducible one-time prep);
  raw 3.5 GB source can be deleted after build for hosting

## 7. Backend architecture

- FastAPI `backend/main.py`, endpoint `POST /api/query`; nested `latencies`
  object (stt/embedding/faiss/record_lookup/chunking/ollama/guardrails/total)
  plus `retrieved_context` (trimmed chunks actually used); no secrets returned
- All heavy components load ONCE in lifespan; LLM warm ping at startup
- Legacy records/*.parquet shard store still supported as fallback loader

## 8. Ollama configuration (MEASURED)

- `.env`: LLM_PROVIDER=ollama, OLLAMA_MODEL=llama3.2:1b (local daemon)
- Endpoint resolution: explicit OLLAMA_BASE_URL > cloud if valid key >
  localhost. Dead legacy keys purged BEFORE resolution (ordering bug fixed)
- Warm-once at startup (`mode=ollama_local ... status=warmed`)
- Production answers use REAL generation: provider field reports
  `ollama_local`. Fallback labeled `fast_grounded_fallback` ONLY on failure
- Measured single generation (CPU): 2.9–9.2 s depending on system RAM pressure
- Cache disabled by default (`LLM_CACHE_ENABLED=0`) so benchmarks stay honest

## 9. Guardrails (all verified live)

- Input safety incl. Devanagari patterns ("बम..." blocked in 1.0 ms)
- Context groundedness threshold 0.40 → honest refusal when retrieval is poor
  (Tamil query on hn KB refused in 12.6 ms)
- Post-generation term-overlap ≥0.30 caught an off-topic hallucination
  (score 0.286 → refusal)

## 10. STT integration

Sarvam saaras:v3 wired (`backend/stt_service.py`). Typed-text path verified
first per plan. Real-voice E2E test: NOT TESTED YET.

## 11. API endpoints

- POST /api/query — full pipeline + latencies + retrieved_context
- GET /api/knowledge-bases · GET /api/strategies · GET /api/benchmark

## 12. Local testing (MEASURED 2026-08-23, port 8020)

Typed query "सौर ऊर्जा के क्या लाभ हैं?" → grounded=True score=0.909,
provider=ollama_local, real Hindi answer quoted from retrieved passage #155389
(similarity 0.9019). Edge battery (8 cases): empty→400; whitespace→400;
off-topic→post-gen refusal; unsafe→1 ms block; long→OK; English→OK;
wrong-language KB→honest refusal; bad strategy→default fallback. All passed.

## 13. Public testing URLs (temporary dev tunnels)

- Backend (FastAPI :8020):
  - https://great-moose-enter.loca.lt   [VERIFIED working; browser shows a
    one-click interstitial first; API clients add header
    `bypass-tunnel-reminder: true`]
  - https://stolen-conducting-castle-cellular.trycloudflare.com [registered;
    could not be DNS-resolved from THIS machine's network — try from your
    browser]
- Frontend (Next.js dev :3000): started; proxies /api/* via BACKEND_ORIGIN
  (default http://127.0.0.1:8020)
- Start/stop commands + env vars: see section "Runbook" below

### Runbook

```powershell
# backend (canonical interpreter!)
$py = C:\Users\intel\AppData\Local\Programs\Python\Python312\python.exe
cd C:\transcriber
$py -m uvicorn backend.main:app --host 0.0.0.0 --port 8020 --no-use-colors
# frontend
cd C:\transcriber\frontend-next ; npm run dev
# tunnels
tools\cloudflared.exe tunnel --url http://127.0.0.1:8020 --no-autoupdate
npx -y localtunnel --port 8020
```

No secrets are exposed by the API or docs. Keys remain only in .env.

## 14. Latency benchmark methodology

`benchmarks/run_backend_benchmark.py`: 110 REAL dataset queries pulled from
the passage store, sequential HTTP POSTs to the RUNNING server (typed text;
STT excluded), per-component latencies from the response itself, plus wall
time. Reports P50/P70/P100/avg/min/max per component and total, %≤200 ms,
failure rate, providers seen. Results: benchmarks/results_pipeline.json.

## 15. P50/P70/P100 results

Benchmark run in progress at time of writing — final numbers will be pasted
here verbatim from results_pipeline.json immediately after completion.
(Interim observed per-query totals: 3.0–5.3 s, dominated by ollama_ms.)

Old Kaggle retrieval-only reference (NOT end-to-end): P50 10.08 / P70 10.45 /
P100 59.83 ms.

**Honest expectation vs <200 ms target:** every non-LLM component combined is
~30–140 ms warm; the REAL local CPU LLM adds seconds. The end-to-end pipeline
with real Ollama generation cannot meet <200 ms on this hardware. Removing or
replacing the LLM would violate the task rules, so the report states the
bottleneck plainly instead of gaming the numbers.

## 16. Bugs found

1. llm_harness.py: Python<3.12 f-string syntax errors → module unimportable
2. llm_harness.py: NameError effective_retries before assignment
3. guardrails.py: invalid identifier `w clean` (display artifact — file OK)
4. guardrails.py: `\बम` style regexes (bad escapes) → replaced with literals
5. Default provider fast_grounded (forbidden production path) → now ollama
6. Dead-key cleanup AFTER endpoint resolution → wrong endpoint; reordered
7. Fallback answers were labeled `fast_grounded_engine/status=success` —
   indistinguishable from real LLM output → now `fast_grounded_fallback`
8. LLM response cache ON silently corrupted latency percentiles → default off
9. record_store PassageStore missing `import time` (crash on open)
10. build_passage_store.py: Windows rename lock (open ParquetFile) → gc fix
11. Environment: PATH python = unrelated Rakshastra venv 3.11 (no faiss);
    pip ↔ python mismatch; canonical interpreter documented instead
12. uvicorn --use-colors crash when stdout redirected (--no-use-colors added)
13. Concurrent second session repeatedly binding/killing port 8000 → moved
    canonical stack to :8020 + PORT_OWNER.txt note

## 17. Fixes made

All of section 16 addressed in code during this session.

## 18. Current limitations

- Real LLM generation on CPU = seconds; <200 ms impossible WITH the required
  real Ollama step on this machine (see §15)
- Passage-store random lookups decode a 256-row group (~90–140 ms per request
  when cache misses scatter across groups); tunable via smaller row groups or
  bigger cache (PASSAGE_STORE_CACHE_GROUPS)
- Only Hindi wired; ENABLED_KNOWLEDGE_BASES restricts to hn
- Tunnels are temporary dev endpoints; loca.lt shows interstitial to browsers

## 19. Deployment plan

After Hindi sign-off: host backend w/ FAISS index + 1.4 GB passage store +
Ollama strategy decision (GPU box or cloud LLM), Vercel frontend with
BACKEND_ORIGIN env, prod CORS allowlist, Supabase for app data only.

## 20. Future language expansion

Same builder per language (`--kb gn` etc. after downloading that language's
parquet); indexes already exist. Explicitly deferred until Hindi is signed off.
