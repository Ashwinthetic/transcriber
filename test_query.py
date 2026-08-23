import os, sys
sys.path.insert(0, r'C:\transcriber\backend')
os.chdir(r'C:\transcriber')
os.environ['ENABLED_KNOWLEDGE_BASES'] = 'hn'
from backend.retrieval import FAISSRetriever
r = FAISSRetriever()
print('Testing query with missing record store...')
chunks, lat, comp = r.retrieve_from_kb("सौर ऊर्जा के क्या फायदे हैं?", lang="hn", top_k=3)
print(f'Chunks returned: {len(chunks)}')
print(f'Latency: {lat:.2f} ms')
print(f'Components: {comp}')
if chunks:
    for c in chunks:
        print(f'  - {c["text"][:100]}...')
else:
    print('  (No chunks - record store missing as expected)')