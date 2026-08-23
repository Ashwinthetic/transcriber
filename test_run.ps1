param()
$p = & "C:\transcriber\backend\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,'C:\transcriber\backend'); from backend.retrieval import FAISSRetriever; r=FAISSRetriever(); print('kb_indexes:', list(r.kb_indexes.keys())); [print(k, v['total_vectors'], v['record_store'].available) for k,v in r.kb_indexes.items()]"
Write-Host $p