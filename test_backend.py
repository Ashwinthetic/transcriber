import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_hindi_rag():
    print("=" * 60)
    print("⚡ TESTING VOICE RAG BACKEND (HINDI KB & SUB-200MS SLA)")
    print("=" * 60)

    payload = {
        "query": "सौर ऊर्जा के क्या लाभ हैं?",
        "strategy": "sentence_based",
        "stt_provider": "sarvam",
        "top_k": 3,
        "lang": "hn"
    }

    print(f"\n📤 Sending Query Request:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        t_start = time.perf_counter()
        res = requests.post(f"{BASE_URL}/api/query", json=payload, timeout=10)
        t_end = time.perf_counter()
        
        if res.status_code == 200:
            data = res.json()
            print("\n✅ API Response Received:")
            print(f"• Query: {data.get('query')}")
            print(f"• Answer: {data.get('answer')}")
            print(f"• Grounded: {data.get('grounded')} (Score: {data.get('grounding_score', 0):.4f})")
            print(f"• Language: {data.get('lang')}")
            print(f"• LLM Provider: {data.get('llm_provider')} ({data.get('llm_model')})")
            print("\n⏱️ Latency Breakdown:")
            print(f"  - STT Latency:         {data.get('stt_latency_ms', 0):.2f} ms (Excluded from Backend SLA)")
            print(f"  - Vector Retrieval:    {data.get('retrieval_latency_ms', 0):.2f} ms")
            print(f"  - Safety & Grounding:  {data.get('guardrail_latency_ms', 0):.2f} ms")
            print(f"  - LLM Generation:      {data.get('llm_latency_ms', 0):.2f} ms")
            print(f"  ----------------------------------------")
            print(f"  ⚡ Backend Latency:     {data.get('backend_latency_ms', 0):.2f} ms")
            print(f"  🎯 Sub-200ms SLA Met:   {'✅ YES' if data.get('latency_target_met') else '❌ NO'}")
        else:
            print(f"❌ Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_hindi_rag()
