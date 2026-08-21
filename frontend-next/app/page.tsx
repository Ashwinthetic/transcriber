"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import MatchboxIntro from "./components/MatchboxIntro";
import Navbar from "./components/Navbar";
import BenchmarkRibbon from "./components/BenchmarkRibbon";
import HeroVoice from "./components/HeroVoice";
import ConfigPanel from "./components/ConfigPanel";
import QueryInput from "./components/QueryInput";
import ResultsPanel, { type QueryResult } from "./components/ResultsPanel";
import VectorInspector from "./components/VectorInspector";
import styles from "./page.module.css";

interface BenchmarkData {
  P50_ms: number;
  P70_ms: number;
  P100_ms: number;
  under_200ms_percentage: number;
  total_queries_tested: number;
}

export default function Home() {
  const [introComplete, setIntroComplete] = useState(false);
  const [benchData, setBenchData] = useState<BenchmarkData | null>(null);
  const [activeStrategy, setActiveStrategy] = useState("sentence_based");
  const [sttProvider, setSttProvider] = useState("sarvam");
  const [lang, setLang] = useState("en-IN");
  const [queryText, setQueryText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Fetch benchmarks on mount
  useEffect(() => {
    fetch("/api/benchmark")
      .then((r) => r.json())
      .then((d) => setBenchData(d))
      .catch(() => {});
  }, []);

  // Run RAG query
  const runQuery = useCallback(
    async (text?: string, audioB64?: string) => {
      const q = text || queryText;
      if (!q && !audioB64) return;
      setLoading(true);
      try {
        const res = await fetch("/api/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: audioB64 ? null : q,
            audio_base64: audioB64 || null,
            strategy: activeStrategy,
            stt_provider: sttProvider,
            top_k: 3,
          }),
        });
        if (!res.ok) throw new Error("API error");
        const data: QueryResult = await res.json();
        setResult(data);
        setQueryText(data.query);
      } catch {
        console.error("Query failed");
      } finally {
        setLoading(false);
      }
    },
    [queryText, activeStrategy, sttProvider]
  );

  // Mic recording
  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      // Stop
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      // Start
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        const mr = new MediaRecorder(stream);
        audioChunksRef.current = [];
        mr.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };
        mr.onstop = () => {
          const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
          const reader = new FileReader();
          reader.onloadend = () => {
            const b64 = (reader.result as string).split(",")[1];
            runQuery(undefined, b64);
          };
          reader.readAsDataURL(blob);
          stream.getTracks().forEach((t) => t.stop());
        };
        mr.start();
        mediaRecorderRef.current = mr;
        setIsRecording(true);
      } catch {
        // Mic unavailable — fall back to text query
        runQuery(
          queryText || "What are the advantages of solar energy?"
        );
      }
    }
  }, [isRecording, runQuery, queryText]);

  return (
    <>
      {!introComplete && (
        <MatchboxIntro onComplete={() => setIntroComplete(true)} />
      )}

      <div
        className={styles.appWrapper}
        style={{ opacity: introComplete ? 1 : 0, transition: "opacity 0.5s ease" }}
      >
        <Navbar />

        <BenchmarkRibbon data={benchData} />

        <div className={styles.gridContainer}>
          {/* Left Column — Voice Input Studio */}
          <div className={styles.leftCol}>
            <div className={styles.cardHeader}>
              <h2 className={styles.sectionTitle}>🎙️ Voice Input Studio</h2>
              <span className="retro-badge badge-green">Sarvam AI Ready</span>
            </div>

            <HeroVoice
              isRecording={isRecording}
              onToggleRecording={toggleRecording}
            />

            <ConfigPanel
              activeStrategy={activeStrategy}
              onStrategyChange={setActiveStrategy}
              sttProvider={sttProvider}
              onSttChange={setSttProvider}
              lang={lang}
              onLangChange={setLang}
            />

            <QueryInput
              value={queryText}
              onChange={setQueryText}
              onSubmit={() => runQuery()}
              loading={loading}
            />
          </div>

          {/* Right Column — Results */}
          <div className={styles.rightCol}>
            <ResultsPanel result={result} loading={loading} />

            <VectorInspector
              chunks={result?.retrieved_chunks ?? []}
              strategy={activeStrategy}
            />
          </div>
        </div>

        <footer className={styles.footer}>
          Built for HH Goa 2026 · Powered by Sarvam AI saaras:v3 · FAISS Vector Engine · MSMARCO-XI
        </footer>
      </div>
    </>
  );
}
