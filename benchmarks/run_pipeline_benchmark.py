import os
import sys
import time
import json
import asyncio
import numpy as np
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.retrieval import FAISSRetriever
from backend.stt_service import SpeechToTextService
from backend.guardrails import RAGGuardrails
from backend.llm_harness import LLMHarness


async def run_pipeline_benchmark(
    num_queries: int = 100,
    lang: str = "hn",
    use_live_llm: bool = False,
    sample_prompts: List[str] = None,
):
    """Runs an end-to-end pipeline benchmark measuring per-component latencies.

    Components measured (each as array of latencies across queries):
      - stt_ms: simulated STT (sample_prompt provided)
      - embed_ms: query embedding with e5-small
      - search_ms: FAISS IVF-PQ ANN search
      - lookup_ms: record-store parquet text lookup
      - chunk_ms: candidate-stage multi-strategy chunking
      - guardrail_ms: input safety + context groundedness
      - llm_ms: LLM harness answer generation
      - total_ms: end-to-end sum (excludes simulated STT if desired)

    If record shards are not available locally for <lang>, lookup_ms will be
    reported as N/A and the benchmark will flag that the numbers are partial
    until the msmarco_xi_full/<lang>/records/*.parquet shards arrive from
    Kaggle notebook output.
    """
    print(f"🚀 Starting Pipeline Benchmark: {num_queries} queries, lang={lang}")
    t_total_start = time.perf_counter()

    eval_file = os.path.join(os.path.dirname(__file__), "eval_queries.json")
    with open(eval_file, "r", encoding="utf-8") as f:
        eval_queries = json.load(f)

    # Select queries: prefer real dataset queries from record store if available,
    # otherwise fall back to the provided sample prompts or a Hindi seed set.
    retriever = FAISSRetriever()
    kb_data = retriever.kb_indexes.get(lang)
    record_store_available = kb_data is not None and kb_data.get("record_store", object()).available if kb_data else False

    queries: List[str] = []
    seen = set()

    # Try to pull real queries from the record store first (if shards exist)
    if record_store_available and hasattr(retriever, "kb_indexes") and retriever.kb_indexes.get(lang):
        try:
            rs = retriever.kb_indexes[lang]["record_store"]
            counted = 0
            for qobj in rs.iter_queries(limit=num_queries * 3, unique_only=True):
                q = (qobj.get("query") or "").strip()
                if q and q not in seen:
                    queries.append(q)
                    seen.add(q)
                    counted += 1
                if len(queries) >= num_queries:
                    break
            if counted == 0:
                raise ValueError("No queries pulled")
        except Exception as e:
            print(f"⚠️ Could not pull queries from record store ({e}); falling back to seed set.")

    # Fallback seed Hindi questions (replace with dataset queries once shards arrive)
    if len(queries) < num_queries:
        seed_hindi = [
            "सौर ऊर्जा के क्या फायदे हैं?",
            "दिल्ली की राजधानी क्या है?",
            "पानी कैसे उबालते हैं?",
            "हिमांसुत्र कैसे बनते हैं?",
            "मONSOON कब आता है?",
            "ट्रेन कैसे चलती है?",
            "बिजली कैसे पैदा होती है?",
            "बाढ़ क्यों आती है?",
            "मृदा अपरदन कैसे रोकें?",
            "प्रदूषण कम कैसे करें?",
            "बाढ़ से कैसे बचें?",
            "ग्लोबल वार्मिंग का कारण क्या है?",
        ]
        for q in seed_hindi:
            if q not in seen:
                queries.append(q)
                seen.add(q)
        print(f"📝 Using {len(seed_hindi)} seeded Hindi questions (shards not yet available).")

    # Augment with eval set if still short
    for q in eval_queries:
        if len(queries) >= num_queries:
            break
        tq = (q or "").strip()
        if tq and tq not in seen:
            queries.append(tq)
            seen.add(tq)

    # If still short, add sample prompts
    if sample_prompts:
        for q in sample_prompts:
            if len(queries) >= num_queries:
                break
            tq = (q or "").strip()
            if tq and tq not in seen:
                queries.append(tq)
                seen.add(tq)

    # Final fallback: use eval queries alone
    if len(queries) < num_queries:
        # duplicate remaining from eval set
        for q in eval_queries:
            if len(queries) >= num_queries:
                break
            tq = (q or "").strip()
            if tq and tq not in seen:
                queries.append(tq)
                seen.add(tq)

    # If still not enough, repeat queries to hit num_queries
    while len(queries) < num_queries:
        for q in queries:
            if len(queries) >= num_queries:
                break
            if q not in seen:
                queries.append(q)
                seen.add(q)

    # Trim to exactly num_queries
    queries = queries[:num_queries]

    print(f"📋 Running {len(queries)} queries (seed+Hindi+eval).")

    stt_svc = SpeechToTextService()
    llm_harness = LLMHarness()
    retriever2 = FAISSRetriever()

    # Per-query latency accumulators
    stt_latencies = []
    embed_latencies = []
    search_latencies = []
    lookup_latencies = []
    chunk_latencies = []
    guardrail_latencies = []
    llm_latencies = []
    total_latencies = []

    detailed_records = []

    print("\n⚡ Running pipeline latency benchmark suite...\n")

    strategy = os.getenv("ACTIVE_CHUNKING_STRATEGY", "sentence_based")

    for idx, q in enumerate(queries):
        q = q.strip()
        if not q:
            continue

        # --- 1. STT (simulated via sample prompt) ---
        stt_res, stt_lat = await stt_svc.transcribe_audio(
            audio_bytes=b"benchmark_audio",
            sample_prompt=q,
        )
        stt_latencies.append(stt_lat)

        # --- 2. Input Safety Guardrail ---
        t_g1 = time.perf_counter()
        safe, msg = RAGGuardrails.check_input_safety(q)
        g1_lat = (time.perf_counter() - t_g1) * 1000.0

        # --- 3. FAISS Retrieval (embed + search + record lookup + chunking) ---
        t_ret_start = time.perf_counter()
        chunks, ret_lat, comp = retriever2.retrieve_with_components(
            query=q, strategy=strategy, top_k=3, lang=lang
        )
        embed_latencies.append(comp.get("embed", 0.0))
        search_latencies.append(comp.get("search", 0.0))
        lookup_latencies.append(comp.get("lookup", "N/A" if not record_store_available else 0.0))
        chunk_latencies.append(comp.get("chunk", 0.0))

        # --- 4. Context Groundedness Guardrail ---
        t_g2 = time.perf_counter()
        grounded, g_score, g_msg = RAGGuardrails.check_context_groundedness(q, chunks)
        g2_lat = (time.perf_counter() - t_g2) * 1000.0

        # --- 5. LLM Answer Generation ---
        if use_live_llm:
            llm_res, llm_lat = await llm_harness.generate_answer(
                query=q, retrieved_chunks=chunks)
        else:
            # fast_grounded default path (no network, deterministic latency)
            llm_res, llm_lat = await llm_harness.generate_answer(
                query=q, retrieved_chunks=chunks)

        llm_latencies.append(llm_lat)

        # --- 6. Post-generation answer groundedness check ---
        t_g3 = time.perf_counter()
        answer_grounded, ans_score, ans_msg = RAGGuardrails.check_answer_groundedness(
            llm_res.get("answer", ""), chunks)
        guard_lat = (time.perf_counter() - t_g3) * 1000.0

        # Accumulate per-query totals
        guardrail_latencies.append(g1_lat + g2_lat + guard_lat)  # input + context + answer grounded
        # total end-to-end (excluding simulated STT for the "backend only" view,
        # but we include it for completeness; user can subtract)
        query_total = stt_lat + g1_lat + ret_lat + g2_lat + llm_lat + guard_lat
        total_latencies.append(query_total)

        record = {
            "query_id": idx + 1,
            "query": q,
            "stt_ms": round(stt_lat, 2),
            "embed_ms": round(comp.get("embed", 0.0), 2),
            "search_ms": round(comp.get("search", 0.0), 2),
            "lookup_ms": round(comp.get("lookup", "N/A"), 2),
            "chunk_ms": round(comp.get("chunk", 0.0), 2),
            "guardrail_ms": round(g1_lat + g2_lat + guard_lat, 2),
            "llm_ms": round(llm_lat, 2),
            "total_ms": round(query_total, 2),
            "under_200ms": query_total <= 200.0,
            "grounded": answer_grounded,
            "strategy": strategy,
        }
        detailed_records.append(record)

    # --- Compute percentiles ---
    def percentiles(arr):
        if not arr:
            return {"p50": 0, "p70": 0, "p100": 0, "avg": 0, "min": 0, "max": 0}
        arr_s = np.sort(arr)
        return {
            "p50": float(np.percentile(arr_s, 50)),
            "p70": float(np.percentile(arr_s, 70)),
            "p100": float(np.max(arr_s)),
            "avg": float(np.mean(arr_s)),
            "min": float(np.min(arr_s)),
            "max": float(np.max(arr_s)),
        }

    report = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "num_queries_tested": len(total_latencies),
        "record_store_available": record_store_available,
        "lang": lang,
        "strategy": strategy,
        "target_ms": 200.0,
        "stt": percentiles(stt_latencies),
        "embed": percentiles(embed_latencies),
        "search": percentiles(search_latencies),
        "lookup": percentiles(lookup_latencies),
        "chunk": percentiles(chunk_latencies),
        "guardrail": percentiles(guardrail_latencies),
        "llm": percentiles(llm_latencies),
        "total": percentiles(total_latencies),
        "under_200ms_count": int(np.sum(np.array(total_latencies) <= 200.0)),
        "under_200ms_percentage": (int(np.sum(np.array(total_latencies) <= 200.0)) / len(total_latencies) * 100) if total_latencies else 0.0,
        "sample_evaluations": detailed_records[:20],
    }

    # Save results
    results_file = os.path.join(os.path.dirname(__file__), "results_pipeline.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    t_total = time.perf_counter() - t_total_start
    print(f"\n📊 === Pipeline Benchmark Results ===")
    print(f"Total Queries: {report['num_queries_tested']}")
    print(f"Record Store Available: {record_store_available}")
    print(f"🎯 P50 Latency (Median): {report['total']['p50']:.2f} ms")
    print(f"🎯 P70 Latency:          {report['total']['p70']:.2f} ms")
    print(f"🎯 P100 Latency (Max):   {report['total']['p100']:.2f} ms")
    print(f"✅ Under 200ms Compliance: {report['under_200ms_percentage']:.1f}% "
          f"({report['under_200ms_count']}/{report['num_queries_tested']})")
    print(f"\nPer-component P50 (ms):")
    for comp_name in ["stt", "embed", "search", "lookup", "chunk", "guardrail", "llm", "total"]:
        p = report[comp_name]
        print(f"  {comp_name:12s} P50={p['p50']:.2f}  P70={p['p70']:.2f}  P100={p['p100']:.2f}  avg={p['avg']:.2f}  min={p['min']:.2f}  max={p['max']:.2f}")

    if not record_store_available:
        print("\n⚠️ Benchmark note: Record shards (knowledge_base/hn/records/*.parquet) "
              "not found. lookup_ms = N/A. Numbers are partial — once the Kaggle notebook "
              "outputs are downloaded (msmarco_xi_full/{hi,gu}/records/*.parquet), re-run "
              "the benchmark for full E2E component breakdown.")

    print(f"\n🎉 Results saved to {results_file}!")
    print(f"Total benchmark runtime: {t_total:.1f}s")

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline RAG Latency Benchmark")
    parser.add_argument("--queries", type=int, default=100, help="Number of queries to test")
    parser.add_argument("--lang", type=str, default="hn", help="Knowledge base language (hn/gu)")
    parser.add_argument("--live-llm", action="store_true", help="Use live LLM API instead of fast_grounded")
    parser.add_argument("--strategy", type=str, default="sentence_based", help="Chunking strategy")
    parser.add_argument("--sample-prompts", nargs="+", help="Extra sample prompts to include")
    args = parser.parse_args()
    asyncio.run(run_pipeline_benchmark(
        num_queries=args.queries,
        lang=args.lang,
        use_live_llm=args.live_llm,
        strategy=args.strategy,
        sample_prompts=args.sample_prompts,
    ))