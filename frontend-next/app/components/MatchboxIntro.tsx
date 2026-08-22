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
      style={{ pointerEvents: "auto", backdropFilter: "blur(15px)" }}
    >
      <div className="matchbox-outer" style={{ position: "relative", border: "1px solid rgba(255,255,255,0.2)", borderRadius: "24px", boxShadow: "0 25px 50px -12px rgba(0,0,0,0.7)", overflow: "hidden" }}>
        
        {/* Background image for the outer box */}
        <img 
          src="/assets/hackers.png" 
          alt="Hackers" 
          style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: 0.15 }} 
        />
        
        <div ref={innerRef} className="matchbox-inner" style={{ 
          position: "relative", 
          zIndex: 2, 
          background: "linear-gradient(135deg, rgba(4, 56, 29, 0.85) 0%, rgba(12, 94, 54, 0.95) 100%)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: "20px"
        }}>
          
          <img 
            src="/assets/goa_hindi.svg" 
            alt="Goa" 
            style={{ width: "80px", marginBottom: "20px", filter: "drop-shadow(0 0 15px rgba(253, 225, 0, 0.6))" }} 
          />
          
          <div ref={titleRef} className="matchbox-title" style={{ 
            color: "var(--goa-sun-yellow)", 
            textShadow: "0 0 20px rgba(253, 225, 0, 0.4)",
            letterSpacing: "2px"
          }}>
            TRANSCRIBER
          </div>
          
          <div ref={subRef} className="matchbox-sub" style={{ 
            color: "rgba(255, 255, 255, 0.9)",
            letterSpacing: "3px",
            marginTop: "8px",
            fontWeight: "500",
            textShadow: "0 2px 4px rgba(0,0,0,0.5)"
          }}>
            VOICE RAG · FAISS · SARVAM AI
          </div>
          
          <img 
            src="/assets/Hacker house.png" 
            alt="Hacker House" 
            style={{ position: "absolute", bottom: "24px", height: "24px", opacity: 0.9, filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.5))" }} 
          />
        </div>
      </div>
    </div>
  );
}
