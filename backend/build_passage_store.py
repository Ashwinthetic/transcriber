"""One-time builder: compact Hindi passage store from ai4bharat/MSMARCO-XI.

Reads train/hintrain.parquet (vector id == local_id == row ordinal, verified
against knowledge_base/hn/config.json) and writes a zstd-compressed parquet
with small row groups containing ONLY the columns the retrieval pipeline needs:

    local_id, query, answer, query_type, target_lang,
    translated_passages, is_selected

English passages / meta / Eng_* columns are dropped (they are never used by
the request path). The raw source file can be deleted afterwards.

Usage:
    python backend/build_passage_store.py --kb hn [--source data/source/hintrain.parquet]
"""

import os
import sys
import json
import hashlib
import argparse
import time

import pyarrow as pa
import pyarrow.parquet as pq

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROW_GROUP_SIZE = 256
BATCH_ROWS = 20000


def digest_batch(tbl) -> str:
    h = hashlib.sha256()
    q = tbl.column("query").to_pylist()
    a = tbl.column("answer").to_pylist()
    tp = tbl.column("translated_passages").to_pylist()
    sel = tbl.column("is_selected").to_pylist()
    for i in range(len(q)):
        h.update((q[i] or "").encode("utf-8"))
        h.update(b"\x00")
        h.update((a[i] or "").encode("utf-8"))
        h.update(b"\x00")
        for p in (tp[i] or []):
            h.update(p.encode("utf-8"))
            h.update(b"\x01")
        h.update(json.dumps(sel[i] or []).encode())
        h.update(b"\x02")
    n_pass = sum(len(x or []) for x in tp)
    n_chars = sum(len(p) for x in tp for p in (x or []))
    return h.hexdigest(), n_pass, n_chars


def convert_batch(batch: pa.RecordBatch, start_id: int) -> pa.Table:
    passages_struct = batch.column("passages")
    tp = passages_struct.field("Translated_passages")
    sel = passages_struct.field("is_selected")
    tbl = pa.table({
        "local_id": pa.array(range(start_id, start_id + batch.num_rows), type=pa.int64()),
        "query": batch.column("query"),
        "answer": batch.column("Answer"),
        "query_type": batch.column("query_type"),
        "target_lang": batch.column("target_lang"),
        "translated_passages": tp,
        "is_selected": sel,
    })
    return tbl


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default="hn")
    ap.add_argument("--source", default=os.path.join("data", "source", "hintrain.parquet"))
    args = ap.parse_args()

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = args.source if os.path.isabs(args.source) else os.path.join(root, args.source)
    out_dir = os.path.join(root, "knowledge_base", args.kb, "passage_store")
    out_path = os.path.join(out_dir, "passages.parquet")

    if not os.path.isfile(src):
        print(f"ERROR: source parquet not found: {src}")
        sys.exit(1)

    kb_config_path = os.path.join(root, "knowledge_base", args.kb, "config.json")
    expected_rows = None
    if os.path.exists(kb_config_path):
        with open(kb_config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if cfg.get("source_file", "").endswith("hintrain.parquet") and cfg.get("language") == "hi":
            expected_rows = int(cfg["source_rows"])
            print(f"KB config expects {expected_rows:,} source rows — will verify")

    os.makedirs(out_dir, exist_ok=True)
    tmp_path = out_path + ".building"

    t0 = time.perf_counter()
    src_pf = pq.ParquetFile(src)
    total_rows = src_pf.metadata.num_rows
    print(f"source: {src} | rows={total_rows:,}")
    if expected_rows is not None and total_rows != expected_rows:
        print(f"FATAL: source rows {total_rows:,} != KB index rows {expected_rows:,} — refusing to build a mismatched store")
        sys.exit(1)

    digests_in = []
    stats_rows = 0
    stats_pass = 0
    stats_chars = 0
    selected_total = 0

    schema = None
    writer = None

    first = True
    done = 0
    for batch in src_pf.iter_batches(batch_size=BATCH_ROWS):
        tbl = convert_batch(batch, done)
        if first:
            writer = pq.ParquetWriter(tmp_path, tbl.schema, compression="zstd")
            first = False
        d, np_, nc = digest_batch(tbl)
        digests_in.append(d)
        stats_rows += tbl.num_rows
        stats_pass += np_
        stats_chars += nc
        for slist in tbl.column("is_selected").to_pylist():
            selected_total += sum(1 for v in (slist or []) if v == 1)
        writer.write_table(tbl, row_group_size=ROW_GROUP_SIZE)
        done += tbl.num_rows
        pct = done * 100.0 / total_rows
        print(f"  converted {done:,}/{total_rows:,} rows ({pct:.1f}%) elapsed={time.perf_counter()-t0:.0f}s")
    writer.close()

    print(f"verifying written store...")
    out_pf = pq.ParquetFile(tmp_path)
    assert out_pf.metadata.num_rows == total_rows, "row count mismatch after write"
    digests_out = []
    for otbl in out_pf.iter_batches(batch_size=BATCH_ROWS, columns=["local_id","query","answer","query_type","target_lang","translated_passages","is_selected"]):
        d, _, _ = digest_batch(pa.Table.from_batches([otbl]))
        digests_out.append(d)
    ok = digests_in == digests_out
    print(f"integrity check: {'PASS' if ok else 'FAIL'} ({len(digests_in)} batches)")

    if not ok:
        print("FATAL: verification failed; keeping source, removing partial store")
        os.remove(tmp_path)
        sys.exit(1)

    if os.path.exists(out_path):
        os.remove(out_path)
    os.rename(tmp_path, out_path)

    size_bytes = os.path.getsize(out_path)
    manifest = {
        "kind": "compact_passage_store",
        "kb": args.kb,
        "dataset": "ai4bharat/MSMARCO-XI",
        "source_file": "train/hintrain.parquet",
        "source_sha256_batches_verified": True,
        "rows": int(stats_rows),
        "row_group_size": ROW_GROUP_SIZE,
        "columns": ["local_id", "query", "answer", "query_type", "target_lang", "translated_passages", "is_selected"],
        "store_bytes": size_bytes,
        "store_mb": round(size_bytes / (1024 * 1024), 1),
        "total_passages": int(stats_pass),
        "avg_passages_per_row": round(stats_pass / max(stats_rows, 1), 3),
        "avg_chars_per_row": round(stats_chars / max(stats_rows, 1), 1),
        "selected_passages": int(selected_total),
        "built_seconds": round(time.perf_counter() - t0, 1),
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"DONE: {out_path}")


if __name__ == "__main__":
    main()
