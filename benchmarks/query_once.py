import json
import os
import sys
import time

import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE = os.getenv("BENCH_BASE", "http://127.0.0.1:8000")


def query(q: str, top_k: int = 3):
    t0 = time.perf_counter()
    r = httpx.post(f"{BASE}/api/query", json={"query": q, "lang": "hn", "strategy": "sentence_based", "top_k": top_k}, timeout=150.0)
    wall = (time.perf_counter() - t0) * 1000
    r.raise_for_status()
    return r.json(), wall


if __name__ == "__main__":
    res, wall = query("सौर ऊर्जा के क्या लाभ हैं?")
    print("WALL_MS:", round(wall, 1))
    print("provider:", res["llm_provider"], "| grounded:", res["grounded"], "| score:", round(res["grounding_score"], 3))
    print("latencies:", json.dumps(res["latencies"]))
    print("ANSWER:", res["answer"][:220])
    print("CTX[0]:", res["retrieved_context"][0]["text"][:160])
