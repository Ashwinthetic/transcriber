import os, sys
sys.path.insert(0, r'C:\transcriber\backend')
os.chdir(r'C:\transcriber')
os.environ['ENABLED_KNOWLEDGE_BASES'] = 'hn'
from backend.retrieval import FAISSRetriever
r = FAISSRetriever()
print('KB indexes:', list(r.kb_indexes.keys()))
for k, v in r.kb_indexes.items():
    sr = v['record_store']
    print(f'  {k}: vectors={v["total_vectors"]}, nprobe={v.get("nprobe")}, records_available={sr.available}')