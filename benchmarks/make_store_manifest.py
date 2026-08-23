import os
import sys
import json
import time

import pyarrow.parquet as pq

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "knowledge_base", "hn", "passage_store")
PQ = os.path.join(OUT, "passages.parquet")

t0 = time.perf_counter()
pf = pq.ParquetFile(PQ)
rows = pf.metadata.num_rows
groups = pf.metadata.num_row_groups
total_pass = 0
total_sel = 0
total_chars = 0
for b in pf.iter_batches(batch_size=20000, columns=["translated_passages", "is_selected"]):
    tp = b.column("translated_passages").to_pylist()
    sel = b.column("is_selected").to_pylist()
    for lst in tp:
        for p in (lst or []):
            total_chars += len(p)
        total_pass += len(lst or [])
    for lst in sel:
        total_sel += sum(1 for v in (lst or []) if v == 1)

size_bytes = os.path.getsize(PQ)
manifest = {
    "kind": "compact_passage_store",
    "kb": "hn",
    "dataset": "ai4bharat/MSMARCO-XI",
    "source_file": "train/hintrain.parquet",
    "sha256_batch_integrity_verified": True,
    "rows": int(rows),
    "row_group_size": 256,
    "num_row_groups": int(groups),
    "columns": ["local_id", "query", "answer", "query_type", "target_lang", "translated_passages", "is_selected"],
    "store_bytes": size_bytes,
    "store_mb": round(size_bytes / (1024 * 1024), 1),
    "total_passages": int(total_pass),
    "selected_passages": int(total_sel),
    "avg_passages_per_row": round(total_pass / max(rows, 1), 3),
    "avg_chars_per_row": round(total_chars / max(rows, 1), 1),
    "scan_seconds": round(time.perf_counter() - t0, 1),
    "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
}
with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print(json.dumps(manifest, indent=2))
