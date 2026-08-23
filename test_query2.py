import os, sys
sys.path.insert(0, r'C:\transcriber\backend')
os.chdir(r'C:\transcriber')
os.environ['ENABLED_KNOWLEDGE_BASES'] = 'hn'
from backend.retrieval import FAISSRetriever
r = FAISSRetriever()

# First query (slow - model load)
print("=== Query 1 (first load) ===")
chunks, lat, comp = r.retrieve_from_kb("सौर ऊर्जा के क्या फायदे हैं?", lang="hn", top_k=3)
print(f'Chunks: {len(chunks)}, Latency: {lat:.2f} ms, Components: {{k: round(v,2) for k,v in comp.items()}}')

# Second query (fast - cached model)
print("\n=== Query 2 (cached model) ===")
chunks, lat, comp = r.retrieve_from_kb("भारत की राजधानी क्या है?", lang="hn", top_k=3)
print(f'Chunks: {len(chunks)}, Latency: {lat:.2f} ms, Components: {{k: round(v,2) for k,v in comp.items()}}')

# Third query
print("\n=== Query 3 ===")
chunks, lat, comp = r.retrieve_from_kb("पानी कैसे उबालते हैं?", lang="hn", top_k=3)
print(f'Chunks: {len(chunks)}, Latency: {lat:.2f} ms, Components: {{k: round(v,2) for k,v in comp.items()}}')