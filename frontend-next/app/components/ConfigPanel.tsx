"use client";

import { motion } from "framer-motion";
import styles from "./ConfigPanel.module.css";

const strategies = [
  {
    id: "sentence_based",
    title: "Sentence-Based",
    desc: "Punctuation boundary splitting",
  },
  {
    id: "fixed_size",
    title: "Fixed-Size",
    desc: "368 char window (50 overlap)",
  },
  {
    id: "semantic",
    title: "Semantic",
    desc: "Cosine similarity shift splits",
  },
  {
    id: "metadata_aware",
    title: "Metadata Aware",
    desc: "Embeds doc_id & category",
  },
];

interface ConfigPanelProps {
  activeStrategy: string;
  onStrategyChange: (s: string) => void;
  sttProvider: string;
  onSttChange: (p: string) => void;
  lang: string;
  onLangChange: (l: string) => void;
}

export default function ConfigPanel({
  activeStrategy,
  onStrategyChange,
  sttProvider,
  onSttChange,
  lang,
  onLangChange,
}: ConfigPanelProps) {
  return (
    <motion.div
      className={styles.panel}
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.8, duration: 0.4 }}
    >
      {/* STT & Language Row */}
      <div className={styles.fieldRow}>
        <div className={styles.fieldCol}>
          <label className="section-label">STT Provider</label>
          <select
            className="retro-select"
            value={sttProvider}
            onChange={(e) => onSttChange(e.target.value)}
          >
            <option value="sarvam">Sarvam AI (saaras:v3)</option>
            <option value="elevenlabs">ElevenLabs STT</option>
          </select>
        </div>
        <div className={styles.fieldCol}>
          <label className="section-label">Language</label>
          <select
            className="retro-select"
            value={lang}
            onChange={(e) => onLangChange(e.target.value)}
          >
            <option value="unknown">🌐 Auto-Detect (Multilingual &amp; Hinglish)</option>
            <option value="hi-IN">Hindi (hi-IN)</option>
            <option value="en-IN">English (en-IN)</option>
            <option value="ta-IN">Tamil (ta-IN)</option>
            <option value="te-IN">Telugu (te-IN)</option>
          </select>
        </div>
      </div>

      {/* Chunking Strategy */}
      <div className={styles.stratSection}>
        <div className={styles.stratHeader}>
          <label className="section-label">Chunking Strategy Engine</label>
          <span className={styles.evalLink}>Evaluation Requirement</span>
        </div>
        <div className={styles.stratGrid}>
          {strategies.map((s) => (
            <motion.button
              key={s.id}
              className={`${styles.stratPill} ${
                activeStrategy === s.id ? styles.active : ""
              }`}
              onClick={() => onStrategyChange(s.id)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              layout
            >
              {activeStrategy === s.id && (
                <motion.div
                  className={styles.activeBackdrop}
                  layoutId="activeStrat"
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              )}
              <span className={styles.stratTitle}>{s.title}</span>
              <span className={styles.stratDesc}>{s.desc}</span>
            </motion.button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
