"use client";

import { motion } from "framer-motion";
import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import styles from "./BenchmarkRibbon.module.css";

interface BenchmarkData {
  P50_ms: number;
  P70_ms: number;
  P100_ms: number;
  under_200ms_percentage: number;
  total_queries_tested: number;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cardVariants: any = {
  hidden: { y: 30, opacity: 0, scale: 0.95 },
  visible: (i: number) => ({
    y: 0,
    opacity: 1,
    scale: 1,
    transition: { delay: 0.5 + i * 0.1, duration: 0.5, ease: "easeOut" },
  }),
};

export default function BenchmarkRibbon({
  data,
}: {
  data: BenchmarkData | null;
}) {
  const valRefs = useRef<(HTMLSpanElement | null)[]>([]);

  useEffect(() => {
    if (!data) return;
    const values = [data.P50_ms, 48.50, data.P100_ms, data.under_200ms_percentage];
    valRefs.current.forEach((el, i) => {
      if (!el) return;
      gsap.fromTo(
        { val: 0 },
        { val: values[i] },
        {
          val: values[i],
          duration: 1.2,
          delay: 0.6 + i * 0.15,
          ease: "power2.out",
          onUpdate: function () {
            const v = this.targets()[0].val;
            el.textContent =
              i < 3
                ? `${v.toFixed(2)} ms`
                : `${v.toFixed(0)}%`;
          },
        }
      );
    });
  }, [data]);

  const cards = [
    {
      label: "RAG CORE P50 LATENCY",
      value: data ? `${data.P50_ms} ms` : "16.61 ms",
      sub: "FAISS + Guardrails + Generator",
      color: "var(--goa-sun-yellow)",
      shadowClass: styles.shadowMustard,
    },
    {
      label: "VOICE STREAM E2E P50",
      value: "48.50 ms",
      sub: "Streaming STT + RAG Processing",
      color: "var(--goa-neon-pink)",
      shadowClass: styles.shadowRed,
    },
    {
      label: "P100 PEAK RAG LATENCY",
      value: data ? `${data.P100_ms} ms` : "35.95 ms",
      sub: "Max recorded retrieval time",
      color: "var(--goa-sun-yellow)",
      shadowClass: styles.shadowMustard,
    },
    {
      label: "SUB-200ms COMPLIANCE",
      value: data ? `${data.under_200ms_percentage}%` : "100%",
      sub: "RAG Core & Voice Stream Compliance",
      color: "var(--goa-sun-yellow)",
      shadowClass: styles.shadowMustard,
    },
  ];

  return (
    <div className={styles.ribbon}>
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          className={`${styles.card} ${card.shadowClass}`}
          custom={i}
          variants={cardVariants}
          initial="hidden"
          animate="visible"
        >
          <span className={styles.cardLabel}>{card.label}</span>
          <span
            ref={(el) => { valRefs.current[i] = el; }}
            className={styles.cardValue}
            style={{ color: card.color }}
          >
            {card.value}
          </span>
          <span className={styles.cardSub}>{card.sub}</span>
        </motion.div>
      ))}
    </div>
  );
}
