import asyncio
import sys
import time

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, ".")
from backend.llm_harness import LLMHarness


async def main():
    h = LLMHarness()
    print("endpoint:", h._get_ollama_url(), "| model:", h.ollama_model)
    warm = await h.warm_up()
    print("WARMUP:", warm)
    chunks = [{
        "doc_id": "kb_123",
        "title": "सौर ऊर्जा",
        "text": "सौर ऊर्जा एक स्वच्छ और नवीकरणीय ऊर्जा स्रोत है। यह बिजली के बिलों को कम करती है और पर्यावरण में कार्बन उत्सर्जन घटाती है।",
    }]
    t0 = time.perf_counter()
    res, lat = await h.generate_answer("सौर ऊर्जा के क्या लाभ हैं?", chunks)
    print("PROVIDER=", res["provider"], "status=", res["status"], "latency_ms=", round(lat, 1))
    print("ANSWER:", res["answer"][:300])
    if res.get("fallback_reason"):
        print("FALLBACK_REASON:", res["fallback_reason"])
    if res.get("attempts_detail"):
        print("ATTEMPTS:", res["attempts_detail"])


asyncio.run(main())
