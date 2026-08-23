import os, sys, asyncio
sys.path.insert(0, r'C:\transcriber\backend')
os.chdir(r'C:\transcriber')
from backend.llm_harness import LLMHarness

async def test():
    harness = LLMHarness()
    print(f"Preferred provider: {harness.preferred_provider}")
    print(f"Ollama model: {harness.ollama_model}")
    print(f"Ollama base URL: {harness.ollama_base_url}")
    print(f"Is Ollama cloud: {harness._is_ollama_cloud()}")
    
    mock_chunks = [{"title": "Solar Energy", "text": "Solar energy reduces carbon emissions and electricity costs by converting sunlight into power."}]
    res, lat = await harness.generate_answer("What are solar energy benefits?", mock_chunks)
    print(f"\nAnswer: {res['answer']}")
    print(f"Provider: {res['provider']}")
    print(f"Model: {res['model']}")
    print(f"Latency: {lat:.2f} ms")
    print(f"Attempts: {res['attempts']}")

asyncio.run(test())