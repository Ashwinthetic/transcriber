"""Passage store: fast FAISS vector-id -> real passage text layer.

Primary format (built by backend/build_passage_store.py):

    knowledge_base/<kb>/passage_store/passages.parquet
        schema: local_id(int64), query(str), answer(str), query_type(str),
                target_lang(str), translated_passages(list[str]),
                is_selected(list<int64>)
        row order == local_id order == FAISS vector id order
        zstd-compressed parquet with small row groups for cheap random access.

The file is opened once at startup (footer only). Lookups decode only the
touched row group column chunks and an LRU keeps recently decoded groups hot.
Legacy knowledge_base/<kb>/records/records_*.parquet shards remain supported.
"""

import os
import sys
import glob
import json
import bisect
import time
from collections import OrderedDict
from typing import Dict, Any, List, Optional, Iterator

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False


class PassageStore:
    """Compact parquet-backed vector-id -> Hindi passage text store."""

    def __init__(self, path: str, cache_groups: int = 64):
        self.path = path
        self.available = False
        self.total_records = 0
        self.num_row_groups = 0
        self._pf = None
        self._group_rows: List[int] = []
        self._group_offsets: List[int] = []
        self._cache: "OrderedDict[int, Any]" = OrderedDict()
        self._cache_limit = max(4, int(os.getenv("PASSAGE_STORE_CACHE_GROUPS", str(cache_groups))))
        self.cache_hits = 0
        self.cache_misses = 0

        if not PYARROW_AVAILABLE:
            print("⚠️ PassageStore disabled: pyarrow not installed")
            return
        if not os.path.isfile(path):
            return

        try:
            t0 = time.perf_counter()
            self._pf = pq.ParquetFile(path)
            md = self._pf.metadata
            self.total_records = md.num_rows
            self.num_row_groups = md.num_row_groups
            off = 0
            for g in range(self.num_row_groups):
                rows = md.row_group(g).num_rows
                self._group_rows.append(rows)
                self._group_offsets.append(off)
                off += rows
            self.available = True
            self.open_seconds = time.perf_counter() - t0
        except Exception as e:
            print(f"⚠️ PassageStore: failed to open {path}: {e}")

    def _group_for(self, local_id: int) -> Optional[int]:
        g = bisect.bisect_right(self._group_offsets, local_id) - 1
        if g < 0 or g >= self.num_row_groups:
            return None
        if local_id >= self._group_offsets[g] + self._group_rows[g]:
            return None
        return g

    def _table_for_group(self, g: int):
        tbl = self._cache.get(g)
        if tbl is not None:
            self.cache_hits += 1
            self._cache.move_to_end(g)
            return tbl
        self.cache_misses += 1
        tbl = self._pf.read_row_group(g, use_threads=False)
        self._cache[g] = tbl
        if len(self._cache) > self._cache_limit:
            self._cache.popitem(last=False)
        return tbl

    def get(self, local_id: int) -> Optional[Dict[str, Any]]:
        """Returns the source record dict for a FAISS vector id, or None."""
        if not self.available:
            return None
        lid = int(local_id)
        if lid < 0 or lid >= self.total_records:
            return None
        g = self._group_for(lid)
        if g is None:
            return None
        tbl = self._table_for_group(g)
        rec = tbl.slice(lid - self._group_offsets[g], 1).to_pylist()[0]
        passages = rec.get("translated_passages") or []
        selected = rec.get("is_selected") or []
        return {
            "local_id": lid,
            "query_id": 0,
            "query": rec.get("query", "") or "",
            "answer": rec.get("answer", "") or "",
            "query_type": rec.get("query_type", "") or "",
            "source_lang": "",
            "target_lang": rec.get("target_lang", "") or "",
            "english_passages": [],
            "translated_passages": passages,
            "is_selected": selected,
        }

    def contains_range(self, local_id: int) -> bool:
        return self.available and 0 <= int(local_id) < self.total_records

    def iter_queries(self, limit: int = 200, unique_only: bool = True) -> Iterator[Dict[str, Any]]:
        if not self.available:
            return
        seen = set()
        yielded = 0
        for g in range(self.num_row_groups):
            tbl = self._table_for_group(g)
            base = self._group_offsets[g]
            for lid, q in zip(
                range(base, base + tbl.num_rows),
                tbl.column("query").to_pylist(),
            ):
                q = (q or "").strip()
                if unique_only:
                    if q in seen:
                        continue
                    seen.add(q)
                yield {"local_id": lid, "query": q}
                yielded += 1
                if yielded >= limit:
                    return

    def stats(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "kind": "compact_passage_store",
            "path": self.path,
            "total_records": self.total_records,
            "num_row_groups": self.num_row_groups,
            "cached_groups": len(self._cache),
            "cache_limit": self._cache_limit,
        }


class RecordStore:
    """Legacy memory-mapped parquet shard store keyed by FAISS vector id."""

    def __init__(self, records_dir: str):
        self.records_dir = records_dir
        self.available = False
        self.total_records = 0
        self._shard_paths: List[str] = []
        self._shard_mins: List[int] = []
        self._shard_maxs: List[int] = []
        self._shard_tables: Dict[int, Any] = {}
        self._open_shard_limit = 4

        if not PYARROW_AVAILABLE:
            print("⚠️ RecordStore disabled: pyarrow not installed")
            return
        if not os.path.isdir(records_dir):
            return

        paths = sorted(glob.glob(os.path.join(records_dir, "records_*.parquet")))
        if not paths:
            print(f"⚠️ RecordStore: no records_*.parquet shards in {records_dir}")
            return

        for p in paths:
            try:
                pf = pq.ParquetFile(p)
                col = pf.read(columns=["local_id"], use_threads=False).column("local_id").to_pylist()
                if not col:
                    continue
                self._shard_paths.append(p)
                self._shard_mins.append(int(col[0]))
                self._shard_maxs.append(int(col[-1]))
                pf.close()
            except Exception as e:
                print(f"⚠️ RecordStore: failed reading shard header {os.path.basename(p)}: {e}")

        if not self._shard_paths:
            return

        order = sorted(range(len(self._shard_paths)), key=lambda i: self._shard_mins[i])
        self._shard_paths = [self._shard_paths[i] for i in order]
        self._shard_mins = [self._shard_mins[i] for i in order]
        self._shard_maxs = [self._shard_maxs[i] for i in order]
        self.total_records = sum(hi - lo + 1 for lo, hi in zip(self._shard_mins, self._shard_maxs))
        self.available = True

    def _shard_index_for(self, local_id: int) -> Optional[int]:
        i = bisect.bisect_right(self._shard_mins, local_id) - 1
        if i < 0 or local_id > self._shard_maxs[i]:
            return None
        return i

    def _table_for(self, shard_idx: int):
        tbl = self._shard_tables.get(shard_idx)
        if tbl is None:
            if len(self._shard_tables) >= self._open_shard_limit:
                self._shard_tables.pop(next(iter(self._shard_tables)))
            tbl = pq.read_table(
                self._shard_paths[shard_idx],
                memory_map=True,
                use_threads=False,
            )
            self._shard_tables[shard_idx] = tbl
        return tbl

    def get(self, local_id: int) -> Optional[Dict[str, Any]]:
        if not self.available:
            return None
        idx = self._shard_index_for(int(local_id))
        if idx is None:
            return None
        row_off = int(local_id) - self._shard_mins[idx]
        tbl = self._table_for(idx)
        if row_off >= tbl.num_rows:
            return None
        rec = tbl.slice(row_off, 1).to_pylist()[0]
        return {
            "local_id": int(rec["local_id"]),
            "query_id": int(rec.get("query_id", 0)),
            "query": rec.get("query", "") or "",
            "answer": rec.get("answer", "") or "",
            "query_type": rec.get("query_type", "") or "",
            "source_lang": rec.get("source_lang", "") or "",
            "target_lang": rec.get("target_lang", "") or "",
            "english_passages": rec.get("english_passages") or [],
            "translated_passages": rec.get("translated_passages") or [],
            "is_selected": rec.get("is_selected") or [],
        }

    def contains_range(self, local_id: int) -> bool:
        return self.available and self._shard_index_for(int(local_id)) is not None

    def stats(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "kind": "legacy_record_shards",
            "records_dir": self.records_dir,
            "total_records": self.total_records,
            "num_shards": len(self._shard_paths),
            "id_ranges": [
                {"min": lo, "max": hi}
                for lo, hi in zip(self._shard_mins, self._shard_maxs)
            ],
        }

    def iter_queries(self, limit: int = 200, unique_only: bool = True) -> Iterator[Dict[str, Any]]:
        if not self.available:
            return
        seen = set()
        yielded = 0
        for idx in range(len(self._shard_paths)):
            tbl = self._table_for(idx)
            ids = tbl.column("local_id").to_pylist()
            qs = tbl.column("query").to_pylist()
            for off, q in enumerate(qs):
                if unique_only:
                    if q in seen:
                        continue
                    seen.add(q)
                yield {"local_id": int(ids[off]), "query": (q or "").strip()}
                yielded += 1
                if yielded >= limit:
                    return


def load_record_store(kb_dir: str):
    """Loads the best available ID->text layer for a KB directory.

    Prefers the compact passage store (knowledge_base/<kb>/passage_store/
    passages.parquet); falls back to legacy records/*.parquet shards.
    Returns an unavailable dummy when neither exists so callers can report the
    gap honestly instead of fabricating context.
    """
    manifest = os.path.join(kb_dir, "records_manifest.json")
    records_dir = os.path.join(kb_dir, "records")
    if os.path.exists(manifest):
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                m = json.load(f)
            alt = m.get("records_dir")
            if alt and os.path.isdir(alt):
                records_dir = alt
        except Exception:
            pass

    compact_path = os.path.join(kb_dir, "passage_store", "passages.parquet")
    if os.path.isfile(compact_path):
        store = PassageStore(compact_path)
        if store.available:
            return store

    legacy = RecordStore(records_dir)
    if legacy.available:
        return legacy

    class _MissingStore:
        available = False
        total_records = 0

        def get(self, local_id):
            return None

        def contains_range(self, local_id):
            return False

        def stats(self):
            return {
                "available": False,
                "kind": "missing",
                "expected_compact": compact_path,
                "expected_legacy": records_dir,
            }

        def iter_queries(self, limit=200, unique_only=True):
            return iter(())

    return _MissingStore()


if __name__ == "__main__":
    kb_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base"))
    target = sys.argv[1] if len(sys.argv) > 1 else "hn"
    rs = load_record_store(os.path.join(kb_root, target))
    print(json.dumps(rs.stats(), indent=2, ensure_ascii=False))
    if rs.available:
        mid = rs.total_records // 2
        t0 = time.perf_counter()
        rec = rs.get(mid)
        lat = (time.perf_counter() - t0) * 1000.0
        print(f"lookup({mid}) in {lat:.2f} ms")
        if rec:
            print("query:", (rec["query"] or "")[:120])
            print("passages:", len(rec["translated_passages"]))
            if rec["translated_passages"]:
                print("first passage head:", rec["translated_passages"][0][:160])
