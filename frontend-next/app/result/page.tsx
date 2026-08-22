"use client";

import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import ResultsPanel from "../components/ResultsPanel";
import VectorInspector from "../components/VectorInspector";
import { useAppContext } from "../../context/AppContext";
import styles from "../page.module.css";
import React from "react";

export default function ResultPage() {
  const router = useRouter();
  const { result, loading, activeStrategy, setResult, setQueryText } = useAppContext();

  const containerRef = React.useRef<HTMLDivElement>(null);
  const titleRowRef = React.useRef<HTMLDivElement>(null);
  const card1Ref = React.useRef<HTMLDivElement>(null);
  const card2Ref = React.useRef<HTMLDivElement>(null);

  // If there's no result and we're not loading, they probably navigated here directly
  React.useEffect(() => {
    if (!result && !loading) {
      router.push("/questions");
    }
  }, [result, loading, router]);

  // GSAP entrance timeline
  React.useEffect(() => {
    if (!result && !loading) return;

    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    // Title row slides in
    tl.fromTo(
      titleRowRef.current,
      { opacity: 0, y: -20 },
      { opacity: 1, y: 0, duration: 0.5 }
    );

    // First card (Latency & Answer) rises up
    tl.fromTo(
      card1Ref.current,
      { opacity: 0, y: 50, scale: 0.97 },
      { opacity: 1, y: 0, scale: 1, duration: 0.7 },
      "-=0.2"
    );

    // Second card (Vector Inspector) rises up if it exists
    if (card2Ref.current) {
      tl.fromTo(
        card2Ref.current,
        { opacity: 0, y: 50, scale: 0.97 },
        { opacity: 1, y: 0, scale: 1, duration: 0.7 },
        "-=0.35"
      );
    }

    return () => { tl.kill(); };
  }, [result, loading]);

  const handleStartOver = () => {
    // Animate out before navigating
    const tl = gsap.timeline({
      onComplete: () => {
        setResult(null);
        setQueryText("");
        router.push("/questions");
      },
    });

    tl.to(containerRef.current, {
      opacity: 0,
      y: -25,
      duration: 0.3,
      ease: "power2.in",
    });
  };

  return (
    <div ref={containerRef} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div ref={titleRowRef} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", opacity: 0 }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", margin: 0, textShadow: "0 2px 4px rgba(0,0,0,0.5)" }}>Analysis Results</h1>
        <button
          onClick={handleStartOver}
          className="retro-btn retro-btn-secondary"
        >
          Start New Recording ↺
        </button>
      </div>

      {/* Step 3: Latency & Answer */}
      <div ref={card1Ref} className={styles.sectionCard} style={{ opacity: 0 }}>
        <div className={styles.cardHeader}>
          <div>
            <span className={styles.stepBadge}>STEP 3</span>
            <h2 className={styles.sectionTitle}>⚡ Real-Time Latency &amp; Grounded LLM Response</h2>
          </div>
          <span className="retro-badge badge-red">Ollama Nemotron Ultra</span>
        </div>
        <p className={styles.stepDesc}>
          Measures sub-millisecond pipeline latency across STT ➔ FAISS ➔ Guardrails ➔ LLM and displays the language-matched grounded answer.
        </p>
        <ResultsPanel result={result} loading={loading} />
      </div>

      {/* Step 4: Vector Inspector */}
      {result && (
        <div ref={card2Ref} className={styles.sectionCard} style={{ opacity: 0 }}>
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.stepBadge}>STEP 4</span>
              <h2 className={styles.sectionTitle}>🔍 FAISS Vector DB Passage Inspector</h2>
            </div>
            <span className="retro-badge badge-green">Top-K Context</span>
          </div>
          <p className={styles.stepDesc}>
            Inspects exact retrieved MSMARCO knowledge passages, document metadata, and FAISS cosine similarity scores.
          </p>
          <VectorInspector
            chunks={result?.retrieved_chunks ?? []}
            strategy={activeStrategy}
          />
        </div>
      )}
    </div>
  );
}
