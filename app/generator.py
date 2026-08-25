"""Eval-loop adapter exposing this submission's REAL generation pipeline as
the eval suite's app.generator interface (generate_answer).

Replicates backend/main.py's /api/query phases 4-6 against whatever context
the eval suite hands in (its own throwaway-index hits):
  4. RAGGuardrails.check_context_groundedness -> refuse if below threshold
  5. LLMHarness.generate_answer (Ollama Cloud / local / Groq, real .env)
  6. RAGGuardrails.check_answer_groundedness -> the honest `.grounded` signal
     that drives the eval's reliability ("lying factor") check.
"""
import asyncio
import os
import sys
import time
from types import SimpleNamespace

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dotenv import load_dotenv

# The submission reads its LLM config from .env (repo root, or the parent
# workspace folder). Load both without overriding anything already set in
# the process env (e.g. the eval judge's OPENAI_API_KEY).
load_dotenv(os.path.join(_ROOT, ".env"))
load_dotenv(os.path.join(_ROOT, "..", ".env"))

if sys.platform == "win32":
    # Same selector-event-loop policy main.py sets for httpx on Windows.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.guardrails import RAGGuardrails
from backend.llm_harness import LLMHarness

_harness = None


def _get_harness() -> LLMHarness:
    global _harness
    if _harness is None:
        _harness = LLMHarness()
    return _harness


def generate_answer(query: str, results: list) -> SimpleNamespace:
    """query + duck-typed contexts (.text/.source/.score) -> answer object
    with .text / .grounded / .generation_ms / .model."""
    harness = _get_harness()
    chunks = [
        {
            "text": getattr(r, "text", ""),
            "source": getattr(r, "source", ""),
            "similarity_score": float(getattr(r, "score", 0.0)),
        }
        for r in results
    ]

    # Phase 4 — same refusal gate as production: below-threshold context is
    # declined instead of answered (this drives grounded=False on
    # unanswerable queries).
    ctx_ok, ctx_score, ctx_msg = RAGGuardrails.check_context_groundedness(query, chunks)
    if not ctx_ok:
        return SimpleNamespace(
            text=ctx_msg,
            grounded=False,
            generation_ms=0.0,
            model="guardrail-refusal",
        )

    # Phase 5 — real LLM harness call through the submission's own code.
    llm_res, llm_ms = asyncio.run(
        harness.generate_answer(query=query, retrieved_chunks=chunks)
    )
    answer_text = llm_res.get("answer", "")

    # Phase 6 — post-generation hallucination gate, as production does.
    ans_ok, ans_score, _ = RAGGuardrails.check_answer_groundedness(answer_text, chunks)

    return SimpleNamespace(
        text=answer_text,
        grounded=bool(ans_ok),
        generation_ms=float(llm_ms),
        model=str(llm_res.get("model", "unknown")),
    )
