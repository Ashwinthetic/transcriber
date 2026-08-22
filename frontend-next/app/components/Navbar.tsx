"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import styles from "./Navbar.module.css";

export default function Navbar() {
  const navRef = useRef<HTMLElement>(null);
  const brandRef = useRef<HTMLDivElement>(null);
  const pillsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    // 1. Navbar slides down
    tl.fromTo(
      navRef.current,
      { y: -80, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8 }
    );

    // 2. Brand logo and text stagger in
    if (brandRef.current) {
      tl.fromTo(
        brandRef.current.children,
        { x: -20, opacity: 0 },
        { x: 0, opacity: 1, duration: 0.5, stagger: 0.1 },
        "-=0.4"
      );
    }

    // 3. Pills pop in with elastic spring
    if (pillsRef.current) {
      tl.fromTo(
        pillsRef.current.children,
        { scale: 0, opacity: 0, rotation: -10 },
        {
          scale: 1,
          opacity: 1,
          rotation: 0,
          duration: 0.6,
          stagger: 0.1,
          ease: "back.out(1.7)",
          clearProps: "transform",
        },
        "-=0.3"
      );
    }

    return () => { tl.kill(); };
  }, []);

  return (
    <nav ref={navRef} className={styles.navbar} style={{ opacity: 0 }}>
      <div ref={brandRef} className={styles.brand}>
        <div className={styles.logoBox} style={{ border: "none", background: "transparent" }}>
          <img src="/assets/goa_hindi.svg" alt="Goa Logo" style={{ width: "32px", height: "32px" }} />
        </div>
        <div className={styles.brandText}>
          <span className={styles.brandName}>
            TRANSCRIBER{" "}
            <span className={styles.aiBadge}>AI</span>
          </span>
          <span className={styles.brandSub}>
            Speech-to-Text · FAISS Vector DB · MSMARCO-XI
          </span>
        </div>
      </div>

      <div ref={pillsRef} className={styles.pills}>
        <div className={`${styles.pill} ${styles.pillGreen}`}>
          <span className={styles.dot} style={{ background: "#1E4D2B" }} />
          Sarvam AI saaras:v3
        </div>
        <div className={`${styles.pill} ${styles.pillRed}`}>
          <span className={styles.dot} style={{ background: "#E23B22" }} />
          FAISS Vector Engine
        </div>
      </div>
    </nav>
  );
}
