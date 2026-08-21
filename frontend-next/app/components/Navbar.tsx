"use client";

import { motion } from "framer-motion";
import styles from "./Navbar.module.css";

export default function Navbar() {
  return (
    <motion.nav
      className={styles.navbar}
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className={styles.brand}>
        <div className={styles.logoBox}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2L2 7L12 12L22 7L12 2Z"
              fill="var(--chili-red)"
              stroke="var(--ink-black)"
              strokeWidth="1.5"
            />
            <path
              d="M2 17L12 22L22 17"
              stroke="var(--ink-black)"
              strokeWidth="1.5"
            />
            <path
              d="M2 12L12 17L22 12"
              stroke="var(--ink-black)"
              strokeWidth="1.5"
            />
          </svg>
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

      <div className={styles.pills}>
        <motion.div
          className={`${styles.pill} ${styles.pillGreen}`}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: "spring" }}
        >
          <span className={styles.dot} style={{ background: "#1E4D2B" }} />
          Sarvam AI saaras:v3
        </motion.div>
        <motion.div
          className={`${styles.pill} ${styles.pillRed}`}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.4, type: "spring" }}
        >
          <span className={styles.dot} style={{ background: "#E23B22" }} />
          FAISS Vector Engine
        </motion.div>
        <motion.div
          className={`${styles.pill} ${styles.pillMustard}`}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: "spring" }}
        >
          ⚡ Latency Target: &lt;200ms
        </motion.div>
      </div>
    </motion.nav>
  );
}
