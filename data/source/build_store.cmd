@echo off
& "C:\Users\intel\AppData\Local\Programs\Python\Python312\python.exe" "C:\transcriber\backend\build_passage_store.py" --kb hn --source "C:\transcriber\data\source\hintrain.parquet" > "C:\transcriber\data\source\build_store.log" 2>&1
echo EXITCODE %ERRORLEVEL% >> "C:\transcriber\data\source\build_store.log"
