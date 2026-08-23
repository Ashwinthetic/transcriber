import io
import struct
import sys

import pyarrow.parquet as pq
import httpx

URL = "https://huggingface.co/datasets/ai4bharat/MSMARCO-XI/resolve/main/train/hintrain.parquet"


def read_range(client: httpx.Client, url: str, start: int, end: int) -> bytes:
    r = client.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=60.0)
    r.raise_for_status()
    return r.content


def main() -> None:
    with httpx.Client(follow_redirects=True) as client:
        head = client.head(URL, timeout=30.0)
        size = int(head.headers.get("content-length", "0") or head.headers.get("x-linked-size", "0"))
        if not size:
            r = client.get(URL, headers={"Range": "bytes=0-0"}, timeout=30.0)
            cr = r.headers.get("content-range", "")
            size = int(cr.split("/")[-1])
        print(f"remote file size: {size:,} bytes ({size / 1e9:.2f} GB)")

        tail = read_range(client, URL, size - 8, size - 1)
        footer_len = struct.unpack("<I", tail[:4])[0]
        print(f"parquet footer length: {footer_len:,} bytes")

        footer_start = size - 8 - footer_len
        blob = read_range(client, URL, footer_start, size - 1)
        pf = pq.ParquetFile(io.BytesIO(blob))
        md = pf.metadata
        print(f"rows: {md.num_rows:,} | row groups: {md.num_row_groups}")
        print("schema:")
        print(pf.schema_arrow)

        col_stats: dict = {}
        total_compressed = 0
        total_uncompressed = 0
        for rg in range(md.num_row_groups):
            rg_md = md.row_group(rg)
            for c in range(rg_md.num_columns):
                cc = rg_md.column(c)
                name = cc.path_in_schema
                s = col_stats.setdefault(name, {"compressed": 0, "uncompressed": 0})
                s["compressed"] += cc.total_compressed_size
                s["uncompressed"] += cc.total_uncompressed_size
                total_compressed += cc.total_compressed_size
                total_uncompressed += cc.total_uncompressed_size

        print("\nper-column compressed sizes (entire file):")
        for name, s in sorted(col_stats.items(), key=lambda kv: -kv[1]["compressed"]):
            print(f"  {name:28s} {s['compressed'] / 1e9:8.3f} GB compressed | {s['uncompressed'] / 1e9:8.3f} GB uncompressed")

        print(f"\nTOTAL compressed {total_compressed / 1e9:.3f} GB | uncompressed {total_uncompressed / 1e9:.3f} GB")

        keep = ["query", "answer", "query_type", "source_lang", "target_lang", "translated_passages", "is_selected"]
        keep_bytes = sum(col_stats.get(k, {}).get("compressed", 0) for k in keep)
        tp = col_stats.get("translated_passages", {}).get("uncompressed", 0)
        print(f"\nprojected compact-store raw text volume (translated_passages uncompressed): {tp / 1e9:.3f} GB")
        print(f"projected kept-columns compressed parquet equivalent: {keep_bytes / 1e9:.3f} GB")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
