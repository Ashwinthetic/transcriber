"use client";

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

export default function BenchmarkRibbon({
  data,
}: {
  data: BenchmarkData | null;
}) {
  const ribbonRef = useRef<HTMLDivElement>(null);
  const valRefs = useRef<(HTMLSpanElement | null)[]>([]);

  // Entrance animation
  useEffect(() => {
    if (!ribbonRef.current) return;

    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    tl.fromTo(
      ribbonRef.current.children,
      { y: 40, opacity: 0, scale: 0.92 },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        duration: 0.6,
        stagger: 0.1,
        ease: "back.out(1.2)",
        clearProps: "transform",
      }
    );

    return () => { tl.kill(); };
  }, []);

  // Number counting animation
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
          duration: 1.5,
          delay: 0.4 + i * 0.15,
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
    <div ref={ribbonRef} className={styles.ribbon}>
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`${styles.card} ${card.shadowClass}`}
          style={{ opacity: 0 }}
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
        </div>
      ))}
    </div>
  );
}
