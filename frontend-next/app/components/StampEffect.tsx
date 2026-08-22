"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";

export default function StampEffect({
  text,
  color = "var(--forest-green)",
  show,
}: {
  text: string;
  color?: string;
  show: boolean;
}) {
  const stampRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (show && stampRef.current) {
      gsap.fromTo(
        stampRef.current,
        {
          scale: 3,
          rotation: -15,
          opacity: 0,
        },
        {
          scale: 1,
          rotation: -6,
          opacity: 1,
          duration: 0.35,
          ease: "back.out(2)",
        }
      );
    }
  }, [show]);

  if (!show) return null;

  return (
    <div
      ref={stampRef}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 14px",
        border: `3px solid ${color}`,
        borderRadius: 6,
        color: color,
        fontFamily: "var(--font-accent)",
        fontSize: 16,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: 2,
        opacity: 0,
        transformOrigin: "center center",
      }}
    >
      {text}
    </div>
  );
}
