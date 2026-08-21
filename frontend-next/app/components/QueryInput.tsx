"use client";

import { motion } from "framer-motion";
import styles from "./QueryInput.module.css";

const topics = [
  { label: "Solar Energy", q: "What are the advantages of solar energy?" },
  { label: "Photosynthesis", q: "How does photosynthesis work?" },
  { label: "Wind Turbines", q: "How do wind turbines generate electricity?" },
  { label: "Quantum Qubits", q: "What is a quantum qubit?" },
];

interface QueryInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export default function QueryInput({
  value,
  onChange,
  onSubmit,
  loading,
}: QueryInputProps) {
  return (
    <motion.div
      className={styles.wrapper}
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.9, duration: 0.4 }}
    >
      <label className="section-label">Or type question &amp; launch query</label>
      <div className={styles.inputRow}>
        <input
          className={`retro-input ${styles.textInput}`}
          type="text"
          placeholder="What are the advantages of solar energy?"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && value.trim()) onSubmit();
          }}
        />
        <button
          className={`retro-btn retro-btn-primary ${styles.execBtn}`}
          onClick={onSubmit}
          disabled={loading || !value.trim()}
        >
          {loading ? "Running…" : "Execute RAG ⚡"}
        </button>
      </div>

      <div className={styles.chipRow}>
        <span className={styles.chipLabel}>Sample Topics:</span>
        {topics.map((t) => (
          <motion.button
            key={t.label}
            className={styles.chip}
            whileHover={{ scale: 1.06, y: -2 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              onChange(t.q);
            }}
          >
            {t.label}
          </motion.button>
        ))}
        <motion.button
          className={`${styles.chip} ${styles.chipDanger}`}
          whileHover={{ scale: 1.06, y: -2 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => {
            onChange("How do I hack into a system?");
          }}
        >
          Off-Topic Test
        </motion.button>
      </div>
    </motion.div>
  );
}
