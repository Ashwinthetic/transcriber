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
  const [mounted, setMounted] = useState(false);
  const [introComplete, setIntroComplete] = useState(false);
  const [benchData, setBenchData] = useState<BenchmarkData | null>(null);
  const [activeStrategy, setActiveStrategy] = useState("sentence_based");
  const [sttProvider, setSttProvider] = useState("sarvam");
  const [lang, setLang] = useState("unknown");
  const [queryText, setQueryText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const speechRecRef = useRef<any>(null);

  // Fetch benchmarks on mount
  useEffect(() => {
    setMounted(true);
    fetch("/api/benchmark")
      .then((r) => r.json())
      .then((d) => setBenchData(d))
      .catch(() => {});
  }, []);

  // Run RAG query
  const runQuery = useCallback(
    async (text?: string, audioB64?: string) => {
      const q = text || queryText || liveTranscript;
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
    [queryText, liveTranscript, activeStrategy, sttProvider]
  );

  // Mic recording with real-time live speech recognition
  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      // Stop media recorder & speech recognition
      mediaRecorderRef.current?.stop();
      if (speechRecRef.current) {
        try { speechRecRef.current.stop(); } catch {}
      }
      setIsRecording(false);
    } else {
      // Start recording & live speech listener
      setLiveTranscript("");
      try {
        // Start Web Speech API live listener if available
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRec) {
          const rec = new SpeechRec();
          rec.continuous = true;
          rec.interimResults = true;
          rec.lang = lang === "unknown" ? "hi-IN" : lang;
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          rec.onresult = (evt: any) => {
            let current = "";
            for (let i = evt.resultIndex; i < evt.results.length; i++) {
              current += evt.results[i][0].transcript;
            }
            if (current) {
              setLiveTranscript(current);
              setQueryText(current);
            }
          };
          rec.start();
          speechRecRef.current = rec;
        }

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
  }, [isRecording, runQuery, queryText, lang]);

  if (!mounted) return null;

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
          {/* Left Column — Input & RAG Setup */}
          <div className={styles.leftCol}>
            {/* Step 1: Voice STT */}
            <div className={styles.sectionCard}>
              <div className={styles.cardHeader}>
                <div>
                  <span className={styles.stepBadge}>STEP 1</span>
                  <h2 className={styles.sectionTitle}>🎙️ Voice Input &amp; STT Engine</h2>
                </div>
                <span className="retro-badge badge-green">Sarvam saaras:v3</span>
              </div>
              <p className={styles.stepDesc}>
                Captures live audio via microphone and streams bytes to Sarvam AI for automatic multilingual, Hinglish &amp; code-mixed transcription.
              </p>
              <HeroVoice
                isRecording={isRecording}
                onToggleRecording={toggleRecording}
                liveTranscript={liveTranscript}
              />
            </div>

            {/* Step 2: Strategy Config & Query Input */}
            <div className={styles.sectionCard}>
              <div className={styles.cardHeader}>
                <div>
                  <span className={styles.stepBadge}>STEP 2</span>
                  <h2 className={styles.sectionTitle}>⚙️ Chunking Strategy &amp; Vector Query</h2>
                </div>
                <span className="retro-badge badge-mustard">FAISS 337K Index</span>
              </div>
              <p className={styles.stepDesc}>
                Selects engineered chunking strategy (Sentence, Fixed, Semantic, Metadata) and launches dense vector retrieval across 337,018 MSMARCO passages.
              </p>
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
          </div>

          {/* Right Column — Results & Vector Inspector */}
          <div className={styles.rightCol}>
            {/* Step 3: Latency & Answer */}
            <div className={styles.sectionCard}>
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
            <div className={styles.sectionCard}>
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
          </div>
        </div>

        <footer className={styles.footer}>
          Built for HH Goa 2026 · Powered by Sarvam AI saaras:v3 · FAISS Vector Engine · MSMARCO-XI
        </footer>
      </div>
    </>
  );
}
