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
    """Orchestrated LLM Harness supporting Ollama (local/cloud), Groq, Sarvam AI,
    and fast grounded fallback — with retries, timeouts, structured I/O, and fallback."""

    def __init__(self):
        self.sarvam_key = os.getenv("SARVAM_API_KEY", "").strip()
        self.nvidia_key = os.getenv("NVIDIA_API_KEY", "").strip()
        self.ollama_key = os.getenv("OLLAMA_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        # Purge known-dead legacy keys BEFORE endpoint resolution so a stale
        # OLLAMA_API_KEY can never route production traffic to unauthenticated
        # Ollama Cloud instead of the configured local model.
        if self.ollama_key and ("c368ff17" in self.ollama_key or "aJvma" in self.ollama_key):
            self.ollama_key = ""
        self.preferred_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        # Endpoint resolution order:
        #   1. explicit OLLAMA_BASE_URL (respected verbatim)
        #   2. Ollama Cloud when OLLAMA_API_KEY is present
        #   3. local daemon http://localhost:11434
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")
        if not self.ollama_base_url:
            self.ollama_base_url = (
                "https://ollama.com/v1" if self.ollama_key else "http://localhost:11434"
            )
        self._cache_enabled = os.getenv("LLM_CACHE_ENABLED", "0") not in ("0", "false", "False")
        self._cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
        self._max_cache_size = int(os.getenv("LLM_CACHE_MAX_ENTRIES", "256"))

        # Retry / timeout configuration
        self.default_timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "45.0"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
        self.retry_backoff = float(os.getenv("LLM_RETRY_BACKOFF", "0.5"))
        self.warm = False

    def _cache_put(self, key: str, value: Tuple[Dict[str, Any], float]):
        if not self._cache_enabled:
            return
        if len(self._cache) >= self._max_cache_size:
            oldest = next(iter(self._cache))
            self._cache.pop(oldest)
        self._cache[key] = value

    def _is_ollama_cloud(self) -> bool:
        """Check if we're using Ollama Cloud API vs local Ollama."""
        return bool(self.ollama_key) and "ollama.com" in self.ollama_base_url

    def _get_ollama_url(self) -> str:
        """Get the appropriate Ollama API endpoint."""
        if self._is_ollama_cloud():
            return "https://ollama.com/v1/chat/completions"
        # Local Ollama: use /api/generate which works reliably
        return f"{self.ollama_base_url}/api/generate"

    def _get_ollama_headers(self) -> Dict[str, str]:
        """Get headers for Ollama request."""
        if self._is_ollama_cloud():
            return {
                "Authorization": f"Bearer {self.ollama_key}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}

    def _build_prompt(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Build a single prompt for LLM with retrieved context (for /api/generate)."""
        context_parts = []
        for c in retrieved_chunks:
            doc_id = c.get("doc_id", "N/A")
            title = c.get("title", "MSMARCO Document")
            text = c.get("text", "").strip()
            if text:
                context_parts.append(f"--- Document Source [{doc_id}]: {title} ---\n{text}")
        
        context = "\n\n".join(context_parts) if context_parts else "No context available."
        
        system_prompt = (
            "You are Transcriber AI, an expert Voice-Enabled RAG model.\n"
            "1. Answer strictly using facts in Retrieved Context (1-2 short sentences max).\n"
            "2. Do NOT invent, assume, or add outside facts.\n"
            "3. MATCH user language exactly."
        )
        
        user_prompt = f"User Question: {query}\n\nRetrieved Context:\n{context}\n\nAnswer:"
        
        return f"{system_prompt}\n\n{user_prompt}"

    # ------------------------------------------------------------ lifecycle

    async def close(self):
        pass

    async def resolve_mode(self) -> str:
        """Returns 'ollama_cloud' | 'ollama_local' | 'unavailable'."""
        if self._is_ollama_cloud():
            return "ollama_cloud" if self.ollama_key else "unavailable"
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(f"{self.ollama_base_url}/api/tags")
            if r.status_code == 200:
                names = [m.get("name", "") for m in r.json().get("models", [])]
                base = self.ollama_model.split(":")[0]
                if any(n == self.ollama_model or n.split(":")[0] == base for n in names):
                    return "ollama_local"
            return "unavailable_model_not_installed"
        except Exception:
            return "unavailable_local_daemon_down"

    async def warm_up(self) -> Dict[str, Any]:
        """One-time warm ping through the REAL production path so the first user
        request pays no cold-start (DNS/TLS/model-load) cost."""
        t0 = time.perf_counter()
        mode = await self.resolve_mode()
        info: Dict[str, Any] = {"mode": mode, "model": self.ollama_model, "endpoint": self._get_ollama_url()}
        probe_query = "ping"
        probe_chunks = [{"title": "warmup", "text": "warmup"}]
        try:
            url = self._get_ollama_url()
            headers = self._get_ollama_headers()
            if self._is_ollama_cloud():
                payload = {
                    "model": self.ollama_model,
                    "messages": [{"role": "user", "content": "Reply with the single word: ready"}],
                    "temperature": 0.0,
                    "max_tokens": 4,
                }
            else:
                payload = {
                    "model": self.ollama_model,
                    "prompt": "Reply with the single word: ready",
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 4},
                }
            async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if self._is_ollama_cloud() else data.get("response", "")
                )
                info["status"] = "warmed"
                info["probe_reply"] = (content or "")[:30]
                self.warm = True
            else:
                info["status"] = f"warmup_http_{resp.status_code}_fallback_ready"
                info["detail"] = resp.text[:150]
        except Exception as e:
            info["status"] = "warmup_failed_fallback_ready"
            info["detail"] = str(e)[:200]
        info["warm_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
        return info

    # ------------------------------------------------------------ synthesis

    def _fast_grounded_synthesis(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Sub-5ms local grounded answer extraction and synthesis engine (fallback only)."""
        if not retrieved_chunks:
            is_hindi = any('\u0900' <= char <= '\u097F' for char in query)
            if is_hindi:
                return f"प्रदान किए गए नॉलेज बेस में '{query}' के लिए कोई प्रासंगिक संदर्भ नहीं मिला।"
            return f"No relevant context found in MSMARCO knowledge base for '{query}'."

        top_chunk = retrieved_chunks[0]
        text = top_chunk.get("text", "").strip()

        if top_chunk.get("source") == "knowledge_base":
            score = top_chunk.get("similarity_score", 0.0)
            vec_id = top_chunk.get("vector_id", "?")
            lang = top_chunk.get("lang", "hi")
            return (
                f"Retrieved from MSMARCO-XI {lang.upper()} knowledge base "
                f"(passage #{vec_id}, similarity: {score:.4f}). "
                f"{text}"
            )

        q_terms = [
            w.strip("?,!.:;\"'()") for w in query.lower().split()
            if w.strip("?,!.:;\"'()") and len(w.strip("?,!.:;\"'()")) > 1
        ]
        q_set = set(q_terms)

        best_sentence = ""
        best_overlap = 0
        best_chunk_score = 0.0

        for chunk in retrieved_chunks:
            text = chunk.get("text", "").strip()
            sim_score = chunk.get("similarity_score", 0.0)
            if not text:
                continue

            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 10]
            for sent in sentences:
                s_words = set(w.strip("?,!.:;\"'()").lower() for w in sent.split())
                overlap = len(q_set.intersection(s_words)) if q_set else 0
                if overlap > best_overlap or (overlap == best_overlap and sim_score > best_chunk_score and overlap > 0):
                    best_overlap = overlap
                    best_sentence = sent
                    best_chunk_score = sim_score

        if best_sentence and best_overlap > 0:
            return f"{best_sentence}."

        is_hindi = any('\u0900' <= char <= '\u097F' for char in query) or "kya" in query.lower() or "hai" in query.lower()
        if is_hindi:
            return "प्रदान किए गए नॉलेज बेस में इस प्रश्न का उत्तर देने के लिए पर्याप्त जानकारी नहीं मिली।"

        if retrieved_chunks and retrieved_chunks[0].get("similarity_score", 0.0) >= 0.40:
            first_text = retrieved_chunks[0].get("text", "").strip()
            first_sent = first_text.split(".")[0].strip() if first_text else ""
            if first_sent:
                return f"{first_sent}."

        return f"I couldn't find sufficient information in the knowledge base to answer '{query}' accurately."

    # ------------------------------------------------------------ orchestration

    async def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        max_retries: int = None
    ) -> Tuple[Dict[str, Any], float]:
        """Generates grounded answer with real Ollama, retries, timeouts, and fallback."""
        t_start = time.perf_counter()
        if max_retries is None:
            max_retries = self.max_retries

        cache_key = f"{query.strip().lower()}:{len(retrieved_chunks)}"
        if self._cache_enabled and cache_key in self._cache:
            res, cached_lat = self._cache[cache_key]
            t_end = time.perf_counter()
            return {**res, "cached": True}, (t_end - t_start) * 1000.0

        effective_retries = max(0, max_retries)

        # 0. Fast grounded fallback (only when explicitly requested or NO providers available)
        has_local_ollama = bool(self.ollama_base_url) and not self._is_ollama_cloud()
        has_any_provider = bool(self.groq_key) or bool(self.ollama_key) or has_local_ollama
        
        if self.preferred_provider in ["fast_grounded", "fast", "local_fast", "sub200ms"] or not has_any_provider:
            answer = self._fast_grounded_synthesis(query, retrieved_chunks)
            t_end = time.perf_counter()
            lat_ms = (t_end - t_start) * 1000.0
            result = {
                "answer": answer,
                "provider": "fast_grounded_fallback",
                "model": "extractive-fallback",
                "status": "fallback",
                "fallback_reason": (
                    "LLM_PROVIDER forced fast_grounded"
                    if self.preferred_provider in ["fast_grounded", "fast", "local_fast", "sub200ms"]
                    else "no LLM provider configured"
                ),
                "attempts": 1,
                "grounded": True
            }
            self._cache_put(cache_key, (result, lat_ms))
            return result, lat_ms

        attempts: List[Dict[str, Any]] = []

        # 1. Primary: Ollama (local or cloud)
        if (self.ollama_key or has_local_ollama) and effective_retries > 0:
            for attempt in range(1, effective_retries + 1):
                attempt_start = time.perf_counter()
                try:
                    url = self._get_ollama_url()
                    headers = self._get_ollama_headers()
                    
                    # Build request payload
                    if self._is_ollama_cloud():
                        payload = {
                            "model": self.ollama_model,
                            "messages": self._build_messages(query, retrieved_chunks),
                            "temperature": 0.0,
                            "max_tokens": 60
                        }
                    else:
                        # Local Ollama: use /api/generate with prompt format
                        prompt = self._build_prompt(query, retrieved_chunks)
                        payload = {
                            "model": self.ollama_model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": 0.0,
                                "num_predict": 60
                            }
                        }

                    async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                        resp = await client.post(url, headers=headers, json=payload)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if self._is_ollama_cloud():
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        else:
                            content = data.get("response", "")
                        
                        lat = (time.perf_counter() - attempt_start) * 1000.0
                        if content and content.strip():
                            result = {
                                "answer": content.strip(),
                                "provider": "ollama_cloud" if self._is_ollama_cloud() else "ollama_local",
                                "model": self.ollama_model,
                                "status": "success",
                                "attempts": attempt,
                                "grounded": True
                            }
                            self._cache_put(cache_key, (result, lat))
                            return result, lat
                    
                    attempts.append({"provider": "ollama", "status_code": resp.status_code, "lat_ms": (time.perf_counter() - attempt_start) * 1000.0})
                except Exception as e:
                    lat = (time.perf_counter() - attempt_start) * 1000.0
                    attempts.append({"provider": "ollama", "error": str(e), "lat_ms": lat})

        # 2. Secondary: Groq API (if configured)
        if self.groq_key and effective_retries > 0:
            for attempt in range(1, effective_retries + 1):
                attempt_start = time.perf_counter()
                try:
                    async with httpx.AsyncClient(timeout=self.default_timeout) as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.groq_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "llama-3.1-8b-instant",
                                "messages": self._build_messages(query, retrieved_chunks),
                                "temperature": 0.0,
                                "max_tokens": 60
                            }
                        )
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        lat = (time.perf_counter() - attempt_start) * 1000.0
                        if content and content.strip():
                            result = {
                                "answer": content.strip(),
                                "provider": "groq_fast",
                                "model": "llama-3.1-8b-instant",
                                "status": "success",
                                "attempts": attempt,
                                "grounded": True
                            }
                            self._cache_put(cache_key, (result, lat))
                            return result, lat
                    attempts.append({"provider": "groq", "status_code": resp.status_code, "lat_ms": (time.perf_counter() - attempt_start) * 1000.0})
                except Exception as e:
                    lat = (time.perf_counter() - attempt_start) * 1000.0
                    attempts.append({"provider": "groq", "error": str(e), "lat_ms": lat})

        # 3. Fallback to fast grounded synthesis (ONLY after real attempts failed)
        answer = self._fast_grounded_synthesis(query, retrieved_chunks)
        t_end = time.perf_counter()
        lat_ms = (time.perf_counter() - t_start) * 1000.0
        last_err = ""
        if attempts:
            last_attempt = attempts[-1]
            last_err = str(last_attempt.get("error") or f"http {last_attempt.get('status_code')}")
        result = {
            "answer": answer,
            "provider": "fast_grounded_fallback",
            "model": "extractive-fallback",
            "status": "fallback",
            "fallback_reason": last_err or "real LLM unavailable",
            "attempts": len(attempts),
            "attempts_detail": attempts,
            "grounded": True
        }
        self._cache_put(cache_key, (result, lat_ms))
        return result, lat_ms


if __name__ == "__main__":
    import asyncio
    harness = LLMHarness()
    mock_chunks = [{"title": "Solar Energy", "text": "Solar energy reduces carbon emissions and electricity costs by converting sunlight into power."}]
    res, lat = asyncio.run(harness.generate_answer("What are solar energy benefits?", mock_chunks))
    print(f"LLM Answer: '{res['answer']}' (Provider: {res['provider']} | Latency: {lat:.2f} ms | Attempts: {res['attempts']})")