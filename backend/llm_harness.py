import os
import sys
import time
import json
import asyncio
import httpx
from typing import List, Dict, Any, Tuple, Optional

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


class LLMHarness:
    """Real-Ollama-first grounded generation harness.

    Production path (normal /api/query traffic):
        retrieved context -> configured OLLAMA_MODEL via Ollama
        (local daemon preferred, else Ollama Cloud) -> generated answer

    fast_grounded synthesis exists ONLY as failure fallback and is always
    flagged provider='fast_grounded_fallback' so it can never masquerade as a
    real LLM response.
    """

    SYSTEM_PROMPT = (
        "You are Transcriber AI, a grounded Voice RAG assistant for MSMARCO-XI knowledge bases.\n"
        "Rules:\n"
        "1. Answer strictly using facts contained in the Retrieved Context.\n"
        "2. If the context is insufficient, say clearly that the knowledge base does not contain the answer. Never invent facts.\n"
        "3. Reply in the SAME language as the user question (e.g. Hindi question -> Hindi answer).\n"
        "4. Keep the answer concise: 1-3 short sentences."
    )

    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "").strip()
        self.api_key = os.getenv("OLLAMA_API_KEY", "").strip()
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")
        self.cloud_base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com/v1").strip().rstrip("/")
        self.timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "30"))
        self.max_retries = int(os.getenv("OLLAMA_MAX_RETRIES", "2"))
        self.retry_backoff = float(os.getenv("OLLAMA_RETRY_BACKOFF", "0.4"))
        self.keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "30m")
        self.warm_enabled = os.getenv("OLLAMA_WARMUP", "1") not in ("0", "false", "False")
        self.max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "160"))

        self._client: Optional[httpx.AsyncClient] = None
        self.mode = "unresolved"
        self.resolved_base = ""
        self.last_error = ""
        self.warm = False

        if not self.model:
            self.model = "nemotron-3-ultra"

    # ------------------------------------------------------------ lifecycle

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key and self.mode == "cloud":
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=5.0),
                limits=httpx.Limits(max_keepalive_connections=2),
                headers=headers,
            )
        return self._client

    async def close(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def resolve(self) -> str:
        """Resolves the real Ollama endpoint once: local daemon first, cloud second."""
        if not self.warm_enabled:
            pass
        else:
            try:
                client = self._get_client_for_resolution()
                tags = await client.get(f"{self.base_url}/api/tags", timeout=3.0)
                if tags.status_code == 200:
                    names = [m.get("name", "") for m in tags.json().get("models", [])]
                    if any(n == self.model or n.split(":")[0] == self.model.split(":")[0] for n in names):
                        self.mode = "local"
                        self.resolved_base = self.base_url
                        return self.mode
            except Exception as e:
                self.last_error = f"local probe: {e}"

        if self.api_key:
            self.mode = "cloud"
            self.resolved_base = self.cloud_base_url
            return self.mode

        self.mode = "unavailable"
        return self.mode

    def _get_client_for_resolution(self) -> httpx.AsyncClient:
        self.mode = "probing_local"
        return self._get_client()

    async def warm_up(self) -> Dict[str, Any]:
        """One-time warm ping so the first user request pays no cold-start cost."""
        t0 = time.perf_counter()
        mode = await self.resolve()
        info: Dict[str, Any] = {"mode": mode, "model": self.model}
        if mode == "unavailable":
            info["status"] = "no_real_llm_available_fallback_only"
            info["detail"] = self.last_error
            return info
        try:
            res, _lat = await self._ollama_chat(
                query="warmup",
                context_blocks=["warmup"],
                max_tokens=1,
            )
            info["status"] = "warmed"
            info["probe_answer"] = (res.get("answer", "") or "")[:40]
            self.warm = True
        except Exception as e:
            info["status"] = "warmup_failed_fallback_ready"
            info["detail"] = str(e)
            self.last_error = str(e)
        info["warm_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        return info

    # ------------------------------------------------------------- inference

    def _build_user_prompt(self, query: str, context_blocks: List[str]) -> str:
        ctx = "\n\n".join(f"[{i+1}] {b}" for i, b in enumerate(context_blocks))
        return f"User Question: {query}\n\nRetrieved Context:\n{ctx}\n\nAnswer:"

    async def _ollama_chat(
        self,
        query: str,
        context_blocks: List[str],
        max_tokens: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], float]:
        client = self._get_client()
        url = f"{self.resolved_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(query, context_blocks)},
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "stream": False,
        }
        if self.mode == "local":
            payload["keep_alive"] = self.keep_alive
        t0 = time.perf_counter()
        resp = await client.post(url, json=payload)
        lat = (time.perf_counter() - t0) * 1000.0
        if resp.status_code != 200:
            raise RuntimeError(f"ollama http {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        content = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "")
        usage = data.get("usage", {}) or {}
        return {
            "answer": (content or "").strip(),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
            },
        }, lat

    async def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        max_retries: Optional[int] = None,
    ) -> Tuple[Dict[str, Any], float]:
        """Generates the REAL answer through the configured Ollama model.

        Returns ({answer, provider, model, ...}, latency_ms). Falls back to the
        deterministic grounded extractor ONLY if every real attempt fails.
        """
        t_start = time.perf_counter()
        retries = self.max_retries if max_retries is None else max_retries
        context_blocks = []
        for c in retrieved_chunks[:5]:
            t = (c.get("text", "") or "").strip()
            if t:
                context_blocks.append(t[:1200])

        if self.mode == "unresolved":
            await self.resolve()

        attempts: List[Dict[str, Any]] = []
        tries = retries + 1
        last_err = ""
        for attempt in range(1, tries + 1):
            if self.mode == "unavailable":
                break
            try:
                res, lat = await self._ollama_chat(query, context_blocks)
                if res["answer"]:
                    result = {
                        "answer": res["answer"],
                        "provider": f"ollama_{self.mode}",
                        "model": self.model,
                        "endpoint": self.resolved_base,
                        "status": "success",
                        "attempts": attempt,
                        "grounded": True,
                        "usage": res.get("usage"),
                    }
                    return result, (time.perf_counter() - t_start) * 1000.0
                last_err = "empty completion"
                attempts.append({"attempt": attempt, "error": last_err, "lat_ms": round(lat, 1)})
            except Exception as e:
                last_err = str(e)
                attempts.append({"attempt": attempt, "error": last_err[:200]})
                if attempt < tries:
                    await asyncio.sleep(self.retry_backoff * attempt)
                if "connect" in last_err.lower() and self.mode == "local":
                    break

        fb_answer, fb_meta = self._fast_grounded_fallback(query, retrieved_chunks)
        total_lat = (time.perf_counter() - t_start) * 1000.0
        result = {
            "answer": fb_answer,
            "provider": "fast_grounded_fallback",
            "model": "extractive-fallback",
            "endpoint": self.resolved_base,
            "status": "fallback",
            "attempts": len(attempts) + 1,
            "grounded": True,
            "fallback_reason": last_err or self.last_error or "real LLM unavailable",
            "attempts_detail": attempts,
            **fb_meta,
        }
        return result, total_lat

    # -------------------------------------------------------------- fallback

    @staticmethod
    def _fast_grounded_fallback(query: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """Extractive fallback used ONLY when the real LLM fails."""
        meta: Dict[str, Any] = {}
        if not retrieved_chunks:
            is_hindi = any('\u0900' <= ch <= '\u097F' for ch in query)
            if is_hindi:
                return "प्रदान किए गए नॉलेज बेस में इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली।", meta
            return "I couldn't find sufficient information in the knowledge base to answer accurately.", meta

        top = retrieved_chunks[0]
        text = (top.get("text", "") or "").strip()
        q_terms = {w.strip("?,!.:;\"'()").lower() for w in query.split() if len(w.strip("?,!.:;\"'()")) > 1}
        best_sent, best_overlap = "", 0
        for chunk in retrieved_chunks:
            ct = (chunk.get("text", "") or "")
            for sent in ct.replace("\n", " ").split("."):
                s = sent.strip()
                if len(s) < 10:
                    continue
                s_words = {w.strip("?,!.:;\"'()").lower() for w in s.split()}
                overlap = len(q_terms & s_words)
                if overlap > best_overlap:
                    best_overlap, best_sent = overlap, s
        if best_sent and best_overlap > 0:
            return f"{best_sent}.", {"fallback_mode": "extractive"}
        is_hindi = any('\u0900' <= ch <= '\u097F' for ch in query)
        if is_hindi:
            return "प्रदान किए गए नॉलेज बेस में इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली।", {"fallback_mode": "refusal"}
        return "I couldn't find sufficient information in the knowledge base to answer accurately.", {"fallback_mode": "refusal"}


if __name__ == "__main__":
    async def _demo():
        h = LLMHarness()
        info = await h.warm_up()
        print(json.dumps(info, ensure_ascii=False))
        chunks = [{"text": "सौर ऊर्जा एक स्वच्छ ऊर्जा स्रोत है जो बिजली के बिलों को कम करता है।"}]
        res, lat = await h.generate_answer("सौर ऊर्जा के क्या लाभ हैं?", chunks)
        print(f"provider={res['provider']} model={res['model']} latency={lat:.0f}ms")
        print("answer:", res["answer"][:200])
        await h.close()

    asyncio.run(_demo())
