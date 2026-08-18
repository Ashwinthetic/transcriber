import os
import sys
import time
import json
import asyncio
import numpy as np
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.retrieval import FAISSRetriever
from backend.stt_service import SpeechToTextService
from backend.guardrails import RAGGuardrails
from backend.llm_harness import LLMHarness


async def run_benchmark_suite():
    print("🚀 Initializing Benchmark Suite for Voice RAG System...")
    
    eval_file = os.path.join(os.path.dirname(__file__), "eval_queries.json")
    with open(eval_file, "r", encoding="utf-8") as f:
        queries = json.load(f)

    print(f"📋 Loaded {len(queries)} evaluation queries.")

    stt_service = SpeechToTextService()
    llm_harness = LLMHarness()
    retriever = FAISSRetriever()

    strategies = ["fixed_size", "sentence_based", "semantic", "metadata_aware"]
    strategy_results: Dict[str, List[float]] = {st: [] for st in strategies}
    all_latencies: List[float] = []

    detailed_records = []

    print("\n⚡ Running Sub-200ms Latency Benchmark Suite...")
    for idx, q in enumerate(queries):
        # Rotate strategy
        st = strategies[idx % len(strategies)]
        
        t_start = time.perf_counter()
        
        # 1. STT (simulated fast audio input)
        stt_res, stt_lat = await stt_service.transcribe_audio(
            audio_bytes=b"benchmark_audio",
            sample_prompt=q
        )
        
        # 2. Input Safety Guardrail
        t_g1_start = time.perf_counter()
        safe, msg = RAGGuardrails.check_input_safety(q)
        g1_lat = (time.perf_counter() - t_g1_start) * 1000.0

        # 3. FAISS Retrieval
        chunks, ret_lat = retriever.retrieve(query=q, strategy=st, top_k=3)

        # 4. Context Grounding Guardrail
        t_g2_start = time.perf_counter()
        grounded, score, g_msg = RAGGuardrails.check_context_groundedness(q, chunks)
        g2_lat = (time.perf_counter() - t_g2_start) * 1000.0
        
        guardrail_tot_lat = g1_lat + g2_lat

        # 5. LLM Answer Generation
        llm_res, llm_lat = await llm_harness.generate_answer(query=q, retrieved_chunks=chunks)

        t_end = time.perf_counter()
        tot_lat = (t_end - t_start) * 1000.0

        strategy_results[st].append(tot_lat)
        all_latencies.append(tot_lat)

        record = {
            "query_id": idx + 1,
            "query": q,
            "strategy": st,
            "stt_ms": round(stt_lat, 2),
            "retrieval_ms": round(ret_lat, 2),
            "guardrail_ms": round(guardrail_tot_lat, 2),
            "llm_ms": round(llm_lat, 2),
            "total_ms": round(tot_lat, 2),
            "under_200ms": tot_lat <= 200.0
        }
        detailed_records.append(record)

    all_latencies_sorted = np.sort(all_latencies)
    
    p50 = float(np.percentile(all_latencies_sorted, 50))
    p70 = float(np.percentile(all_latencies_sorted, 70))
    p100 = float(np.max(all_latencies_sorted))
    under_200_count = int(np.sum(all_latencies_sorted <= 200.0))
    under_200_pct = (under_200_count / len(all_latencies_sorted)) * 100.0

    print("\n📊 === BENCHMARK RESULTS SUMMARY ===")
    print(f"Total Queries Evaluated: {len(all_latencies)}")
    print(f"🎯 P50 Latency (Median): {p50:.2f} ms")
    print(f"🎯 P70 Latency:          {p70:.2f} ms")
    print(f"🎯 P100 Latency (Max):   {p100:.2f} ms")
    print(f"✅ Under 200ms Compliance: {under_200_pct:.1f}% ({under_200_count}/{len(all_latencies)})")

    per_strategy_summary = {}
    for st, lats in strategy_results.items():
        arr = np.array(lats)
        per_strategy_summary[st] = {
            "count": len(arr),
            "p50_ms": round(float(np.percentile(arr, 50)), 2),
            "p70_ms": round(float(np.percentile(arr, 70)), 2),
            "p100_ms": round(float(np.max(arr)), 2),
            "under_200ms_pct": round(float((np.sum(arr <= 200.0) / len(arr)) * 100.0), 1)
        }
        print(f"  • Strategy [{st}]: P50={per_strategy_summary[st]['p50_ms']}ms, P70={per_strategy_summary[st]['p70_ms']}ms, P100={per_strategy_summary[st]['p100_ms']}ms")

    benchmark_output = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_queries_tested": len(queries),
        "P50_ms": round(p50, 2),
        "P70_ms": round(p70, 2),
        "P100_ms": round(p100, 2),
        "target_ms": 200.0,
        "under_200ms_percentage": round(under_200_pct, 1),
        "per_strategy_breakdown": per_strategy_summary,
        "sample_evaluations": detailed_records[:10]
    }

    results_file = os.path.join(os.path.dirname(__file__), "results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_output, f, indent=2)

    print(f"\n🎉 Results saved to {results_file}!")


if __name__ == "__main__":
    asyncio.run(run_benchmark_suite())
