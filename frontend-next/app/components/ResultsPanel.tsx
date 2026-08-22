"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { gsap } from "gsap";
import StampEffect from "./StampEffect";
import styles from "./ResultsPanel.module.css";

export interface QueryResult {
  query: string;
  answer: string;
  grounded: boolean;
  grounding_score: number;
  refusal_reason?: string | null;
  stt_latency_ms: number;
  retrieval_latency_ms: number;
  guardrail_latency_ms: number;
  llm_latency_ms: number;
  total_latency_ms: number;
  latency_target_met: boolean;
  stt_provider: string;
  strategy_used: string;
  retrieved_chunks: Array<{
    text: string;
    title?: string;
    doc_id?: string;
    similarity_score?: number;
  }>;
}

export default function ResultsPanel({
  result,
  loading,
}: {
  result: QueryResult | null;
  loading: boolean;
}) {
  const latNumRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!result || !latNumRef.current) return;
    gsap.fromTo(
      { v: 0 },
      { v: result.total_latency_ms },
      {
        v: result.total_latency_ms,
        duration: 0.8,
        ease: "power2.out",
        onUpdate: function () {
          if (latNumRef.current) {
            latNumRef.current.textContent = this.targets()[0].v.toFixed(1);
          }
        },
      }
    );
  }, [result]);

  const sum = result
    ? result.stt_latency_ms +
      result.retrieval_latency_ms +
      result.guardrail_latency_ms +
      result.llm_latency_ms || 1
    : 1;

  return (
    <motion.div
      className={styles.panel}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.6, duration: 0.5 }}
    >
      <div className={styles.header}>
        <h2 className={styles.title}>⚡ Real-Time Latency &amp; Answer Output</h2>
        {result && (
          <span
            className={`retro-badge ${
              result.latency_target_met ? "badge-green" : "badge-mustard"
            }`}
          >
            {result.latency_target_met
              ? "✓ Sub-200ms Target Passed"
              : "⚠ Over 200ms Target"}
          </span>
        )}
      </div>

      {/* Latency Analytics Box */}
      <div className={styles.latencyBox}>
        <div className={styles.latTop}>
          <div>
            <span
              ref={latNumRef}
              className={styles.latNumber}
            >
              {result ? result.total_latency_ms.toFixed(1) : "0.0"}
            </span>
            <span className={styles.latUnit}> ms Total E2E Latency</span>
          </div>
          <div className={styles.breakdownChips}>
            <span>STT Stream: {result?.stt_latency_ms.toFixed(1) ?? "0"}ms</span>
            <span>FAISS: {result?.retrieval_latency_ms.toFixed(1) ?? "0"}ms</span>
            <span>Guard: {result?.guardrail_latency_ms.toFixed(1) ?? "0"}ms</span>
            <span>LLM: {result?.llm_latency_ms.toFixed(1) ?? "0"}ms</span>
          </div>
        </div>
        {result && (
          <div className={styles.progressTrack}>
            <div
              className={styles.segStt}
              style={{ width: `${(result.stt_latency_ms / sum) * 100}%` }}
              title={`STT: ${result.stt_latency_ms.toFixed(1)}ms`}
            />
            <div
              className={styles.segRet}
              style={{ width: `${(result.retrieval_latency_ms / sum) * 100}%` }}
              title={`FAISS Vector Search: ${result.retrieval_latency_ms.toFixed(1)}ms`}
            />
            <div
              className={styles.segGuard}
              style={{ width: `${(result.guardrail_latency_ms / sum) * 100}%` }}
              title={`Guardrails Check: ${result.guardrail_latency_ms.toFixed(1)}ms`}
            />
            <div
              className={styles.segLlm}
              style={{ width: `${(result.llm_latency_ms / sum) * 100}%` }}
              title={`LLM Generation: ${result.llm_latency_ms.toFixed(1)}ms`}
            />
          </div>
        )}
      </div>

      {/* Transcript */}
      <AnimatePresence mode="wait">
        {result && (
          <motion.div
            key="transcript"
            className={styles.transcriptBox}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <div className={styles.tbHeader}>
              <span>🎙️ Transcribed Voice Query</span>
              <span className={styles.sttMeta}>
                {result.stt_provider === "sarvam"
                  ? "Sarvam saaras:v3"
                  : "ElevenLabs STT"}
              </span>
            </div>
            <p className={styles.tbText}>&ldquo;{result.query}&rdquo;</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Answer */}
      <AnimatePresence mode="wait">
        {loading && (
          <motion.div
            key="loading"
            className={styles.answerBox}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <div className={styles.loadingPulse}>
              ⚡ Executing Voice RAG pipeline… (Sarvam STT → FAISS → Guardrail → LLM)
            </div>
          </motion.div>
        )}
        {result && !loading && (
          <motion.div
            key="answer"
            className={styles.answerBox}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <div className={styles.abHeader}>
              <span>🤖 Grounded LLM Response</span>
              <StampEffect
                text={
                  result.grounded
                    ? `✓ Grounded ${(result.grounding_score * 100).toFixed(0)}%`
                    : "✕ Not Grounded"
                }
                color={
                  result.grounded ? "var(--forest-green)" : "var(--chili-red)"
                }
                show={true}
              />
            </div>
            <p className={styles.abBody}>{result.answer}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      {!result && !loading && (
        <div className={styles.emptyState}>
          <p>🎤 Record a voice query or type a question to see results</p>
        </div>
      )}
    </motion.div>
  );
}
