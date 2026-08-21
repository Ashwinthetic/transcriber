"use client";

import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";

export default function MatchboxIntro({ onComplete }: { onComplete: () => void }) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLDivElement>(null);
  const subRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const tl = gsap.timeline({
      onComplete: () => {
        setVisible(false);
        onComplete();
      },
    });

    // Phase 1: Matchbox slides up revealing content
    tl.fromTo(
      titleRef.current,
      { y: 40, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }
    )
      .fromTo(
        subRef.current,
        { y: 20, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, ease: "power2.out" },
        "-=0.2"
      )
      // Hold
      .to({}, { duration: 0.8 })
      // Phase 2: Inner drawer slides up and away
      .to(innerRef.current, {
        y: "-110%",
        duration: 0.7,
        ease: "power3.inOut",
      })
      // Phase 3: Outer box scales down and fades
      .to(
        overlayRef.current,
        {
          opacity: 0,
          scale: 0.8,
          duration: 0.5,
          ease: "power2.in",
        },
        "-=0.3"
      );
  }, [onComplete]);

  if (!visible) return null;

  return (
    <div
      ref={overlayRef}
      className="matchbox-overlay"
      style={{ pointerEvents: "auto" }}
    >
      <div className="matchbox-outer">
        <div ref={innerRef} className="matchbox-inner">
          <div ref={titleRef} className="matchbox-title">
            TRANSCRIBER
          </div>
          <div ref={subRef} className="matchbox-sub">
            Voice RAG · FAISS · Sarvam AI
          </div>
        </div>
      </div>
    </div>
  );
}
