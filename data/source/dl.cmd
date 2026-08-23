@echo off
curl.exe -sS -L --retry 5 --retry-delay 2 -o "C:\transcriber\data\source\hintrain.parquet" "https://huggingface.co/datasets/ai4bharat/MSMARCO-XI/resolve/main/train/hintrain.parquet" 2> "C:\transcriber\data\source\download_err.log"
echo EXITCODE %ERRORLEVEL% >> "C:\transcriber\data\source\download_err.log"
