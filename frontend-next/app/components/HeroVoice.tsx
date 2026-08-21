"use client";

import { useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { gsap } from "gsap";
import styles from "./HeroVoice.module.css";

interface HeroVoiceProps {
  isRecording: boolean;
  onToggleRecording: () => void;
}

export default function HeroVoice({
  isRecording,
  onToggleRecording,
}: HeroVoiceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number | null>(null);
  const ringRef = useRef<HTMLDivElement>(null);

  const drawWave = useCallback(
    (speaking: boolean) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const bars = 35;
      const barW = 5;
      const gap = 7;
      const startX = (canvas.width - bars * (barW + gap)) / 2;

      for (let i = 0; i < bars; i++) {
        const x = startX + i * (barW + gap);
        const h = speaking
          ? Math.abs(Math.sin(Date.now() * 0.008 + i * 0.5)) * 28 + 6
          : 4;
        const y = (canvas.height - h) / 2;

        ctx.fillStyle = speaking ? "#E23B22" : "#EADCC0";
        ctx.beginPath();
        ctx.roundRect(x, y, barW, h, 2);
        ctx.fill();
      }

      if (speaking) {
        animRef.current = requestAnimationFrame(() => drawWave(true));
      }
    },
    []
  );

  useEffect(() => {
    drawWave(isRecording);
    if (isRecording && ringRef.current) {
      gsap.to(ringRef.current, {
        boxShadow: "0 0 0 12px rgba(226, 59, 34, 0.15)",
        duration: 0.6,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
    } else if (ringRef.current) {
      gsap.killTweensOf(ringRef.current);
      gsap.set(ringRef.current, { boxShadow: "none" });
    }
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [isRecording, drawWave]);

  return (
    <motion.div
      className={styles.heroWrapper}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.7, duration: 0.5 }}
    >
      <div className={styles.heroInner}>
        <div
          ref={ringRef}
          className={`${styles.micRing} ${isRecording ? styles.recording : ""}`}
        >
          <button
            className={styles.micBtn}
            onClick={onToggleRecording}
            aria-label="Toggle voice recording"
          >
            {isRecording ? (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="var(--chili-red)">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg width="28" height="28" viewBox="0 0 24 24" fill="var(--ink-black)">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" stroke="var(--ink-black)" strokeWidth="2" fill="none" strokeLinecap="round" />
                <line x1="12" y1="19" x2="12" y2="23" stroke="var(--ink-black)" strokeWidth="2" strokeLinecap="round" />
                <line x1="8" y1="23" x2="16" y2="23" stroke="var(--ink-black)" strokeWidth="2" strokeLinecap="round" />
              </svg>
            )}
          </button>
        </div>

        <canvas
          ref={canvasRef}
          className={styles.waveCanvas}
          width={420}
          height={50}
        />

        <p className={styles.caption}>
          {isRecording
            ? "Listening… Click mic to stop recording"
            : "Click microphone to record voice prompt"}
        </p>
      </div>
    </motion.div>
  );
}
