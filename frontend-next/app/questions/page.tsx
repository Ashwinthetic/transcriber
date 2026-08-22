"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { gsap } from "gsap";
import ConfigPanel from "../components/ConfigPanel";
import QueryInput from "../components/QueryInput";
import { useAppContext } from "../../context/AppContext";
import styles from "../page.module.css";

export default function QuestionsPage() {
  const router = useRouter();
  const {
    activeStrategy,
    setActiveStrategy,
    sttProvider,
    setSttProvider,
    lang,
    setLang,
    queryText,
    setQueryText,
    loading,
    setResult,
  } = useAppContext();

  const containerRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const descRef = useRef<HTMLParagraphElement>(null);
  const configRef = useRef<HTMLDivElement>(null);
  const queryRef = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline({
      defaults: { ease: "power3.out" },
    });

    // Card container scales in
    tl.fromTo(
      containerRef.current,
      { opacity: 0, y: 40, scale: 0.97 },
      { opacity: 1, y: 0, scale: 1, duration: 0.6 }
    );

    // Header slides in from left
    tl.fromTo(
      headerRef.current,
      { opacity: 0, x: -30 },
      { opacity: 1, x: 0, duration: 0.5 },
      "-=0.3"
    );

    // Description fades up
    tl.fromTo(
      descRef.current,
      { opacity: 0, y: 15 },
      { opacity: 1, y: 0, duration: 0.4 },
      "-=0.2"
    );

    // ConfigPanel slides in from right
    tl.fromTo(
      configRef.current,
      { opacity: 0, x: 30 },
      { opacity: 1, x: 0, duration: 0.5 },
      "-=0.2"
    );

    // QueryInput fades up
    tl.fromTo(
      queryRef.current,
      { opacity: 0, y: 20 },
      { opacity: 1, y: 0, duration: 0.4 },
      "-=0.15"
    );

    // Button pops in with spring
    tl.fromTo(
      btnRef.current,
      { opacity: 0, scale: 0.8, y: 10 },
      { opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "back.out(1.7)" },
      "-=0.15"
    );

    return () => { tl.kill(); };
  }, []);

  const handleProceed = () => {
    // Animate out before navigating
    const tl = gsap.timeline({
      onComplete: () => {
        setResult(null);
        router.push("/record");
      },
    });

    tl.to(containerRef.current, {
      opacity: 0,
      y: -30,
      scale: 0.97,
      duration: 0.35,
      ease: "power2.in",
    });
  };

  return (
    <div ref={containerRef} className={styles.sectionCard} style={{ opacity: 0 }}>
      <div ref={headerRef} className={styles.cardHeader} style={{ opacity: 0 }}>
        <div>
          <span className={styles.stepBadge}>STEP 1</span>
          <h2 className={styles.sectionTitle}>⚙️ Configure &amp; Prepare</h2>
        </div>
        <span className="retro-badge badge-mustard">Setup Context</span>
      </div>
      <p ref={descRef} className={styles.stepDesc} style={{ opacity: 0 }}>
        Select your STT provider, engineered chunking strategy (Sentence, Fixed, Semantic, Metadata) and optionally type a manual text query before proceeding to voice recording.
      </p>
      
      <div ref={configRef} style={{ opacity: 0 }}>
        <ConfigPanel
          activeStrategy={activeStrategy}
          onStrategyChange={setActiveStrategy}
          sttProvider={sttProvider}
          onSttChange={setSttProvider}
          lang={lang}
          onLangChange={setLang}
        />
      </div>
      
      <div ref={queryRef} style={{ opacity: 0 }}>
        <QueryInput
          value={queryText}
          onChange={setQueryText}
          onSubmit={handleProceed}
          loading={loading}
        />
      </div>

      <div ref={btnRef} style={{ marginTop: "1.5rem", display: "flex", justifyContent: "flex-end", opacity: 0 }}>
        <button
          onClick={handleProceed}
          className="retro-btn retro-btn-primary"
        >
          Proceed to Voice Recording ➔
        </button>
      </div>
    </div>
  );
}
