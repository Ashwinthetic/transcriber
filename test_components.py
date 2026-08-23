import os, sys, asyncio
sys.path.insert(0, r'C:\transcriber\backend')
os.chdir(r'C:\transcriber')
os.environ['ENABLED_KNOWLEDGE_BASES'] = 'hn'
from backend.retrieval import FAISSRetriever
from backend.llm_harness import LLMHarness
from backend.guardrails import RAGGuardrails

async def test():
    print('=== Testing Components ===')
    
    # 1. Retriever
    r = FAISSRetriever()
    print('KB loaded:', list(r.kb_indexes.keys()))
    for k, v in r.kb_indexes.items():
        sr = v['record_store']
        print(f'  {k}: vectors={v["total_vectors"]}, records_available={sr.available}')
    
    # 2. Retrieval (missing shards)
    print('\n=== Retrieval Test (missing shards) ===')
    chunks, lat, comp = r.retrieve_from_kb('सौर ऊर्जा के क्या फायदे हैं?', lang='hn', top_k=3)
    print(f'Chunks: {len(chunks)}, Latency: {lat:.1f}ms')
    print('Components:', {k: round(v,1) for k,v in comp.items()})
    
    # 3. Guardrails
    print('\n=== Guardrails Test ===')
    safe, msg = RAGGuardrails.check_input_safety('सौर ऊर्जा के क्या फायदे हैं?')
    print(f'Input safety: {safe}, {msg}')
    grounded, score, msg = RAGGuardrails.check_context_groundedness('test', [])
    print(f'Context groundedness (empty): {grounded}, score={score}')
    
    # 4. LLM Harness
    print('\n=== LLM Test ===')
    harness = LLMHarness()
    mock_chunks = [{'title': 'Solar', 'text': 'Solar energy reduces emissions.'}]
    res, lat = await harness.generate_answer('What are solar benefits?', mock_chunks)
    print(f'Answer: {res["answer"][:100]}...')
    print(f'Provider: {res["provider"]}, Latency: {lat:.1f}ms, Attempts: {res["attempts"]}')

asyncio.run(test())