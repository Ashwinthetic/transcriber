import json
import os
import sys
import time

import httpx
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding="utf-8")

from backend.record_store import load_record_store

BASE = os.getenv("BENCH_BASE", "http://127.0.0.1:8000")
NUM_QUERIES = int(os.getenv("BENCH_QUERIES", "110"))
TOP_K = int(os.getenv("BENCH_TOP_K", "3"))
STRATEGY = os.getenv("BENCH_STRATEGY", "sentence_based")
OUT_PATH = os.path.join(os.path.dirname(__file__), "results_pipeline.json")


def percentiles(arr):
    if not arr:
        return {"p50": 0.0, "p70": 0.0, "p100": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}
    a = np.array(arr, dtype=float)
    return {
        "p50": round(float(np.percentile(a, 50)), 2),
        "p70": round(float(np.percentile(a, 70)), 2),
        "p100": round(float(np.max(a)), 2),
        "avg": round(float(np.mean(a)), 2),
        "min": round(float(np.min(a)), 2),
        "max": round(float(np.max(a)), 2),
    }


def collect_queries(n: int):
    rs = load_record_store(os.path.join("knowledge_base", "hn"))
    assert rs.available, "passage store missing"
    qs, seen = [], set()
    for item in rs.iter_queries(limit=n * 4, unique_only=True):
        q = (item.get("query") or "").strip()
        if len(q) >= 8 and q not in seen:
            qs.append(q)
            seen.add(q)
        if len(qs) >= n:
            break
    return qs


def main():
    t_start = time.perf_counter()
    queries = collect_queries(NUM_QUERIES)
    print(f"collected {len(queries)} real dataset queries from passage store")

    comp_keys = ["stt_ms", "embedding_ms", "faiss_ms", "record_lookup_ms", "chunking_ms", "ollama_ms", "guardrails_ms"]
    series = {k: [] for k in comp_keys}
    series["total_backend_ms"] = []
    series["wall_ms"] = []

    records = []
    failures = []
    providers = {}

    client = httpx.Client(timeout=170.0)
    for i, q in enumerate(queries):
        payload = {"query": q, "lang": "hn", "strategy": STRATEGY, "top_k": TOP_K}
        try:
            w0 = time.perf_counter()
            r = client.post(f"{BASE}/api/query", json=payload)
            wall = (time.perf_counter() - w0) * 1000.0
            r.raise_for_status()
            d = r.json()
            lat = d.get("latencies", {})
            for k in comp_keys:
                series[k].append(float(lat.get(k, 0.0)))
            series["total_backend_ms"].append(float(d.get("total_latency_ms", 0.0)))
            series["wall_ms"].append(wall)
            prov = d.get("llm_provider") or "none"
            providers[prov] = providers.get(prov, 0) + 1
            records.append({
                "i": i + 1,
                "query": q,
                "provider": prov,
                "grounded": d.get("grounded"),
                "total_backend_ms": round(d.get("total_latency_ms", 0.0), 1),
                "latencies": d.get("latencies", {}),
            })
            print(f"[{i+1}/{len(queries)}] total={d.get('total_latency_ms', 0):.0f}ms ollama={lat.get('ollama_ms', 0):.0f}ms faiss={lat.get('faiss_ms', 0):.1f}ms lookup={lat.get('record_lookup_ms', 0):.1f}ms prov={prov}")
        except Exception as e:
            failures.append({"i": i + 1, "query": q, "error": str(e)[:160]})
            print(f"[{i+1}/{len(queries)}] FAILURE: {str(e)[:120]}")

    under_200 = sum(1 for v in series["total_backend_ms"] if v <= 200.0)
    n_ok = len(series["total_backend_ms"])
    report = {
        "status": "success" if n_ok else "failed",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "typed_text_http_end_to_end",
        "stt_mode": "EXCLUDED from these numbers (typed text path); voice measured separately",
        "llm_mode": "REAL Ollama local llama3.2:1b via /api/generate — no fake/deterministic answers counted as LLM",
        "lang": "hn",
        "strategy": STRATEGY,
        "top_k": TOP_K,
        "num_queries_attempted": len(queries),
        "num_queries_succeeded": n_ok,
        "num_failures": len(failures),
        "failure_rate_pct": round(len(failures) * 100.0 / max(len(queries), 1), 2),
        "providers_seen": providers,
        "target_ms": 200.0,
        "components": {k: percentiles(v) for k, v in series.items()},
        "under_200ms_count": under_200,
        "under_200ms_percentage": round(under_200 * 100.0 / max(n_ok, 1), 2),
        "failures": failures[:20],
        "per_query": records,
        "benchmark_wall_seconds": round(time.perf_counter() - t_start, 1),
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n===== SUMMARY =====")
    for k, v in report["components"].items():
        print(f"{k:18s} P50={v['p50']:>9.2f}  P70={v['p70']:>9.2f}  P100={v['p100']:>9.2f}  avg={v['avg']:>9.2f}  min={v['min']:>9.2f}  max={v['max']:>9.2f}")
    print(f"under_200ms: {report['under_200ms_count']}/{n_ok} ({report['under_200ms_percentage']}%)")
    print(f"providers: {providers}")
    print(f"saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
