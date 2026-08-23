@echo off
"C:\Users\intel\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > "C:\transcriber\data\source\server.log" 2>&1
