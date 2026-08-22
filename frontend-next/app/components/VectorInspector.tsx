"use client";

import { motion, Variants } from "framer-motion";
import styles from "./VectorInspector.module.css";

interface Chunk {
  text: string;
  title?: string;
  doc_id?: string;
  similarity_score?: number;
}

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 15 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.35, ease: "easeOut" },
  }),
};

export default function VectorInspector({
  chunks,
  strategy,
}: {
  chunks: Chunk[];
  strategy: string;
}) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <span className={styles.headerLabel}>🔍 Top-K FAISS Vector Chunks</span>
        <span className={styles.stratBadge}>{strategy}</span>
      </div>
      <div className={styles.list}>
        {chunks.length > 0 ? (
          chunks.map((chunk, i) => (
            <motion.div
              key={i}
              className={styles.chunkItem}
              custom={i}
              variants={itemVariants}
              initial="hidden"
              animate="visible"
            >
              <div className={styles.chunkMeta}>
                <span className={styles.chunkTitle}>
                  [#{i + 1}] {chunk.title || chunk.doc_id || `Passage #${i + 1}`}
                </span>
                <span className={styles.chunkScore}>
                  FAISS Cosine Sim:{" "}
                  {chunk.similarity_score !== undefined
                    ? chunk.similarity_score.toFixed(4)
                    : "N/A"}
                </span>
              </div>
              <p className={styles.chunkText}>{chunk.text}</p>
            </motion.div>
          ))
        ) : (
          <div className={styles.empty}>
            No context passages retrieved yet.
          </div>
        )}
      </div>
    </div>
  );
}
