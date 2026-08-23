import os
import sys
import time
import base64
import asyncio
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    # psycopg async mode requires a selector event loop on Windows (kept for any app-data DB use)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from backend.retrieval import FAISSRetriever
from backend.stt_service import SpeechToTextService
from backend.guardrails import RAGGuardrails
from backend.llm_harness import LLMHarness

# Global instances — initialized ONCE at startup, reused for every request.
retriever: Optional[FAISSRetriever] = None
stt_service: Optional[SpeechToTextService] = None
llm_harness: Optional[LLMHarness] = None


def get_retriever_inst() -> FAISSRetriever:
    global retriever
    if retriever is None:
        retriever = FAISSRetriever()
    return retriever


def get_stt_inst() -> SpeechToTextService:
    global stt_service
    if stt_service is None:
        stt_service = SpeechToTextService()
    return stt_service


def get_llm_inst() -> LLMHarness:
    global llm_harness
    if llm_harness is None:
        llm_harness = LLMHarness()
    return llm_harness


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warms the FAISS vector index, record store, embedding model and STT/LLM services.

    All heavy artifacts load ONCE here; the request path only performs
    embed -> FAISS search -> record lookup -> harness -> response.
    """
    print("🚀 Pre-warming RAG Engine components...")
    t_start = time.perf_counter()
    get_stt_inst()
    llm_engine = get_llm_inst()
    engine = get_retriever_inst()
    engine.warm_up()

    llm_warm_info: Dict[str, Any] = {}
    if os.getenv("LLM_WARMUP_ON_START", "1") not in ("0", "false"):
        try:
            llm_warm_info = await llm_engine.warm_up()
        except Exception as e:
            llm_warm_info = {"status": "warmup_error_fallback_ready", "detail": str(e)}
        print(f"🧠 LLM warm-up: {llm_warm_info.get('status')} | mode={llm_warm_info.get('mode')} model={getattr(llm_engine, 'ollama_model', None) or getattr(llm_engine, 'model', None)}")

    t_end = time.perf_counter()
    kbs = ", ".join(engine.kb_indexes.keys()) if engine.kb_indexes else "none"
    print(f"✅ RAG Engine pre-warmed in {(t_end - t_start):.2f}s | knowledge bases: {kbs}")
    yield
    print("🛑 Server shutting down...")
    try:
        await llm_engine.close()
    except Exception:
        pass


app = FastAPI(
    title="Voice RAG Query Engine",
    description="Sub-200ms Voice-Based RAG System grounded on MSMARCO-XI with Sarvam/ElevenLabs STT",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for local development and web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Text query if not using voice")
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded audio bytes")
    strategy: str = Field(default="sentence_based", description="Chunking strategy: passage_aware | fixed_size | sentence_based | semantic | metadata_aware")
    stt_provider: str = Field(default="sarvam", description="STT provider: sarvam | elevenlabs")
    top_k: int = Field(default=3, description="Number of context chunks to retrieve")
    sample_prompt: Optional[str] = Field(default=None, description="Fast test query string")
    lang: str = Field(default="hn", description="Knowledge base language code: hn (Hindi) | gn (Gujarati) | ...")


class QueryResponse(BaseModel):
    query: str
    stt_provider: str
    strategy_used: str
    answer: str
    grounded: bool
    grounding_score: float
    refusal_reason: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    retrieval_backend: str = Field(default="faiss_ivfpq", description="faiss_ivfpq | none")
    stt_latency_ms: float
    retrieval_latency_ms: float
    guardrail_latency_ms: float
    llm_latency_ms: float
    embed_latency_ms: float = 0.0
    vector_search_latency_ms: float = 0.0
    record_lookup_latency_ms: float = 0.0
    candidate_chunk_latency_ms: float = 0.0
    backend_latency_ms: float = Field(description="Backend-only latency (retrieval + guardrails + LLM), excludes STT")
    total_latency_ms: float
    latency_target_met: bool = Field(description="True if total_latency_ms <= 200ms")
    lang: str = Field(default="hn", description="Knowledge base language used")
    latencies: Dict[str, float] = Field(default_factory=dict, description="Per-component latency breakdown (ms): stt, embedding, faiss, record_lookup, chunking, ollama, guardrails, total")
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list, description="Trimmed retrieved context chunks actually used for grounding")


@app.post("/api/query", response_model=QueryResponse)
async def process_voice_rag_query(req: QueryRequest):
    """Executes full end-to-end Voice RAG pipeline with per-component latency breakdown."""
    t_total_start = time.perf_counter()

    stt_svc = get_stt_inst()
    ret_engine = get_retriever_inst()
    llm_engine = get_llm_inst()

    stt_lat = 0.0
    query_text = req.query or ""

    # 1. Speech-to-Text phase
    if req.audio_base64 or req.sample_prompt:
        audio_bytes = base64.b64decode(req.audio_base64) if req.audio_base64 else b"dummy_audio"
        stt_res, stt_lat = await stt_svc.transcribe_audio(
            audio_bytes=audio_bytes,
            provider=req.stt_provider,
            sample_prompt=req.sample_prompt
        )
        query_text = stt_res.get("transcript", query_text)

    if not query_text.strip():
        raise HTTPException(status_code=400, detail="No query text or audio provided.")

    # 2. Input Safety Guardrail phase
    t_guard_start = time.perf_counter()
    safe, safety_msg = RAGGuardrails.check_input_safety(query_text)
    guard_lat = (time.perf_counter() - t_guard_start) * 1000.0

    if not safe:
        tot_lat = (time.perf_counter() - t_total_start) * 1000.0
        return QueryResponse(
            query=query_text,
            stt_provider=req.stt_provider,
            strategy_used=req.strategy,
            answer="I cannot fulfill this request as it violates safety guidelines.",
            grounded=False,
            grounding_score=0.0,
            refusal_reason=safety_msg,
            retrieval_backend="none",
            stt_latency_ms=stt_lat,
            retrieval_latency_ms=0.0,
            guardrail_latency_ms=guard_lat,
            llm_latency_ms=0.0,
            backend_latency_ms=guard_lat,
            total_latency_ms=tot_lat,
            latency_target_met=(tot_lat <= 200.0),
            lang=req.lang,
            latencies={
                "stt_ms": round(stt_lat, 2),
                "embedding_ms": 0.0,
                "faiss_ms": 0.0,
                "record_lookup_ms": 0.0,
                "chunking_ms": 0.0,
                "ollama_ms": 0.0,
                "guardrails_ms": round(guard_lat, 2),
                "total_ms": round(tot_lat, 2),
            },
        )

    # 3. Vector Retrieval phase — local FAISS IVF-PQ index (loaded once at startup)
    chunks, ret_lat, comp = ret_engine.retrieve_with_components(
        query=query_text,
        strategy=req.strategy,
        top_k=req.top_k,
        lang=req.lang
    )
    retrieval_backend = "faiss_ivfpq" if chunks else (
        "faiss_ivfpq" if req.lang in ret_engine.kb_indexes else "none"
    )

    # 4. Context Groundedness Guardrail phase
    t_guard2_start = time.perf_counter()
    grounded, ground_score, ground_msg = RAGGuardrails.check_context_groundedness(query_text, chunks)
    guard_lat += (time.perf_counter() - t_guard2_start) * 1000.0

    if not grounded:
        tot_lat = (time.perf_counter() - t_total_start) * 1000.0
        backend_lat = ret_lat + guard_lat
        return QueryResponse(
            query=query_text,
            stt_provider=req.stt_provider,
            strategy_used=req.strategy,
            answer=ground_msg,
            grounded=False,
            grounding_score=ground_score,
            refusal_reason=ground_msg,
            retrieval_backend=retrieval_backend,
            stt_latency_ms=stt_lat,
            retrieval_latency_ms=ret_lat,
            guardrail_latency_ms=guard_lat,
            llm_latency_ms=0.0,
            embed_latency_ms=comp.get("embed", 0.0),
            vector_search_latency_ms=comp.get("search", 0.0),
            record_lookup_latency_ms=comp.get("lookup", 0.0),
            candidate_chunk_latency_ms=comp.get("chunk", 0.0),
            backend_latency_ms=backend_lat,
            total_latency_ms=tot_lat,
            latency_target_met=(tot_lat <= 200.0),
            lang=req.lang,
            latencies={
                "stt_ms": round(stt_lat, 2),
                "embedding_ms": round(comp.get("embed", 0.0), 2),
                "faiss_ms": round(comp.get("search", 0.0), 2),
                "record_lookup_ms": round(comp.get("lookup", 0.0), 2),
                "chunking_ms": round(comp.get("chunk", 0.0), 2),
                "ollama_ms": 0.0,
                "guardrails_ms": round(guard_lat, 2),
                "total_ms": round(tot_lat, 2),
            },
        )

    # 5. LLM Harness Answer Generation phase
    llm_res, llm_lat = await llm_engine.generate_answer(
        query=query_text,
        retrieved_chunks=chunks
    )

    # 6. Post-generation hallucination check (answer must be grounded in context)
    t_guard3_start = time.perf_counter()
    answer_grounded, ans_score, ans_msg = RAGGuardrails.check_answer_groundedness(llm_res.get("answer", ""), chunks)
    guard_lat += (time.perf_counter() - t_guard3_start) * 1000.0

    tot_lat = (time.perf_counter() - t_total_start) * 1000.0
    backend_lat = ret_lat + guard_lat + llm_lat  # Excludes STT

    final_answer = llm_res.get("answer", "")
    refusal_reason = None if answer_grounded else f"post_generation_ungrounded (score={ans_score:.3f})"

    retrieved_context = [
        {
            "text": (c.get("text", "") or "")[:500],
            "similarity_score": round(float(c.get("similarity_score", 0.0)), 4),
            "vector_id": c.get("vector_id"),
            "doc_id": c.get("doc_id"),
            "strategy": c.get("strategy"),
            "lang": c.get("lang"),
        }
        for c in chunks[: req.top_k]
    ]

    return QueryResponse(
        query=query_text,
        stt_provider=req.stt_provider,
        strategy_used=req.strategy,
        answer=final_answer,
        grounded=answer_grounded,
        grounding_score=ans_score,
        refusal_reason=refusal_reason,
        llm_provider=llm_res.get("provider"),
        llm_model=llm_res.get("model"),
        retrieval_backend=retrieval_backend,
        stt_latency_ms=stt_lat,
        retrieval_latency_ms=ret_lat,
        guardrail_latency_ms=guard_lat,
        llm_latency_ms=llm_lat,
        embed_latency_ms=comp.get("embed", 0.0),
        vector_search_latency_ms=comp.get("search", 0.0),
        record_lookup_latency_ms=comp.get("lookup", 0.0),
        candidate_chunk_latency_ms=comp.get("chunk", 0.0),
        backend_latency_ms=backend_lat,
        total_latency_ms=tot_lat,
        latency_target_met=(tot_lat <= 200.0),
        lang=req.lang,
        latencies={
            "stt_ms": round(stt_lat, 2),
            "embedding_ms": round(comp.get("embed", 0.0), 2),
            "faiss_ms": round(comp.get("search", 0.0), 2),
            "record_lookup_ms": round(comp.get("lookup", 0.0), 2),
            "chunking_ms": round(comp.get("chunk", 0.0), 2),
            "ollama_ms": round(llm_lat, 2),
            "guardrails_ms": round(guard_lat, 2),
            "total_ms": round(tot_lat, 2),
        },
        retrieved_context=retrieved_context,
    )


@app.get("/api/strategies")
def get_chunking_strategies():
    """Lists supported chunking strategies and index stats."""
    ret_engine = get_retriever_inst()
    stats = {}
    for k, v in ret_engine.strategy_indexes.items():
        stats[k] = {
            "total_chunks": v["total_chunks"],
            "faiss_indexed": True,
            "bm25_indexed": True
        }
    return {
        "active_strategies": [
            "passage_aware", "fixed_size", "sentence_based", "semantic", "metadata_aware"
        ],
        "kb_candidate_strategies": {
            "passage_aware": "Whole translated passage per chunk (dataset is passage-aligned)",
            "fixed_size": "Character window with overlap",
            "sentence_based": "Sentence groups (Devanagari-aware boundaries)",
            "semantic": "Embedding-shift boundary detection on sentences",
            "metadata_aware": "Sentence groups prefixed with type/language metadata"
        },
        "sample_strategy_stats": stats,
        "default_strategy": "sentence_based"
    }


@app.get("/api/benchmark")
def get_benchmark_summary():
    """Returns cached or live sub-200ms benchmark statistics."""
    bench_file = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "results_pipeline.json")
    if not os.path.exists(bench_file):
        bench_file = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "results.json")
    if os.path.exists(bench_file):
        try:
            import json
            with open(bench_file, "r") as f:
                return json.load(f)
        except Exception:
            pass

    return {
        "status": "no_benchmark_run_yet",
        "message": "Run benchmarks/run_pipeline_benchmark.py to generate pipeline P50/P70/P100 numbers.",
        "target_ms": 200.0
    }


@app.get("/api/knowledge-bases")
def get_knowledge_bases():
    """Returns info about loaded local FAISS knowledge bases and their record stores."""
    ret_engine = get_retriever_inst()
    kb_list = []
    for kb_key, kb_data in ret_engine.kb_indexes.items():
        store = kb_data.get("record_store")
        kb_list.append({
            "id": kb_key,
            "lang_code": kb_data.get("lang_code", kb_key),
            "total_vectors": kb_data.get("total_vectors", 0),
            "dimension": kb_data.get("dimension", 0),
            "index_type": kb_data.get("index_type", "IVFPQ"),
            "embedding_model": kb_data.get("embedding_model", "unknown"),
            "dataset": kb_data.get("dataset", "unknown"),
            "nprobe": kb_data.get("nprobe"),
            "backend": "local_faiss",
            "record_store": store.stats() if store is not None else {"available": False},
        })

    return {
        "knowledge_bases": kb_list,
        "total_loaded": len(kb_list),
        "retrieval_backend": "local_faiss_ivfpq",
    }


# Serve Frontend Web App
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
