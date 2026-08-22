"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import HeroVoice from "../components/HeroVoice";
import { useAppContext } from "../../context/AppContext";
import type { QueryResult } from "../components/ResultsPanel";
import styles from "../page.module.css";

export default function RecordPage() {
  const router = useRouter();
  const {
    activeStrategy,
    sttProvider,
    lang,
    queryText,
    setQueryText,
    setLoading,
    setResult,
  } = useAppContext();

  const [isRecording, setIsRecording] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const speechRecRef = useRef<any>(null);

  // GSAP refs
  const containerRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const descRef = useRef<HTMLParagraphElement>(null);
  const heroRef = useRef<HTMLDivElement>(null);

  // Entrance animation
  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    tl.fromTo(
      containerRef.current,
      { opacity: 0, y: 50, scale: 0.96 },
      { opacity: 1, y: 0, scale: 1, duration: 0.7 }
    );

    tl.fromTo(
      headerRef.current,
      { opacity: 0, x: -25 },
      { opacity: 1, x: 0, duration: 0.5 },
      "-=0.35"
    );

    tl.fromTo(
      descRef.current,
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.4 },
      "-=0.2"
    );

    // Hero mic section scales in with a spring
    tl.fromTo(
      heroRef.current,
      { opacity: 0, scale: 0.85, y: 20 },
      { opacity: 1, scale: 1, y: 0, duration: 0.7, ease: "back.out(1.4)" },
      "-=0.15"
    );

    return () => { tl.kill(); };
  }, []);

  // Run RAG query
  const runQuery = useCallback(
    async (text?: string, audioB64?: string) => {
      const q = text || queryText || liveTranscript;
      if (!q && !audioB64) return;
      
      setLoading(true);
      router.push("/result");

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
        setResult({
          query: q || "Voice Query",
          answer: "Unable to connect to backend server. Please verify backend service on port 8000 is active.",
          grounded: false,
          grounding_score: 0.0,
          stt_latency_ms: 0,
          retrieval_latency_ms: 0,
          guardrail_latency_ms: 0,
          llm_latency_ms: 0,
          total_latency_ms: 0,
          latency_target_met: false,
          stt_provider: sttProvider,
          strategy_used: activeStrategy,
          retrieved_chunks: []
        });
      } finally {
        setLoading(false);
      }
    },
    [queryText, liveTranscript, activeStrategy, sttProvider, router, setLoading, setResult, setQueryText]
  );

  // Mic recording with real-time live speech recognition
  const toggleRecording = useCallback(async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      if (speechRecRef.current) {
        try { speechRecRef.current.stop(); } catch {}
      }
      setIsRecording(false);
    } else {
      setLiveTranscript("");
      try {
        const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRec) {
          const rec = new SpeechRec();
          rec.continuous = true;
          rec.interimResults = true;
          rec.lang = lang;
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
        runQuery(
          queryText || "What are the advantages of solar energy?"
        );
      }
    }
  }, [isRecording, runQuery, queryText, lang, setQueryText]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (isRecording) {
        mediaRecorderRef.current?.stop();
        if (speechRecRef.current) {
          try { speechRecRef.current.stop(); } catch {}
        }
      }
    };
  }, [isRecording]);

  return (
    <div ref={containerRef} className={styles.sectionCard} style={{ maxWidth: "800px", margin: "0 auto", opacity: 0 }}>
      <div ref={headerRef} className={styles.cardHeader} style={{ opacity: 0 }}>
        <div>
          <span className={styles.stepBadge}>STEP 2</span>
          <h2 className={styles.sectionTitle}>🎙️ Voice Input &amp; STT Engine</h2>
        </div>
        <span className="retro-badge badge-green">Sarvam saaras:v3</span>
      </div>
      <p ref={descRef} className={styles.stepDesc} style={{ opacity: 0 }}>
        Captures live audio via microphone and streams bytes to Sarvam AI for automatic multilingual, Hinglish &amp; code-mixed transcription.
      </p>
      <div ref={heroRef} style={{ opacity: 0 }}>
        <HeroVoice
          isRecording={isRecording}
          onToggleRecording={toggleRecording}
          liveTranscript={liveTranscript}
        />
      </div>
    </div>
  );
}
