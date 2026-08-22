"use client";

import React from "react";
import { motion } from "framer-motion";
import { ReactLenis } from "@studio-freight/react-lenis";
import MatchboxIntro from "./components/MatchboxIntro";
import Navbar from "./components/Navbar";
import BenchmarkRibbon from "./components/BenchmarkRibbon";
import styles from "./page.module.css";
import { useAppContext } from "../context/AppContext";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const { introComplete, setIntroComplete, benchData, mounted } = useAppContext();

  if (!mounted) return null;

  return (
    <ReactLenis root options={{ lerp: 0.08, duration: 1.2, smoothWheel: true }}>
      {!introComplete && (
        <MatchboxIntro onComplete={() => setIntroComplete(true)} />
      )}

      <div
        className={styles.appWrapper}
        style={{ opacity: introComplete ? 1 : 0, transition: "opacity 0.5s ease" }}
      >
        {/* Global Theme Background with slow pan animation */}
        <motion.div 
          style={{ position: "fixed", inset: "-5%", zIndex: -2, pointerEvents: "none" }}
          animate={{
            scale: [1, 1.05, 1],
            rotate: [0, 1, -1, 0],
          }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
        >
          <img
            src="/assets/Sun rise.png"
            alt="Sunrise Background"
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "center", opacity: 0.85 }}
          />
          {/* Animated floating glowing orbs */}
          <motion.div
            style={{
              position: "absolute", top: "20%", left: "10%", width: "300px", height: "300px",
              background: "radial-gradient(circle, rgba(253, 225, 0, 0.4) 0%, rgba(0,0,0,0) 70%)",
              borderRadius: "50%", mixBlendMode: "screen", filter: "blur(40px)"
            }}
            animate={{ x: [0, 50, -50, 0], y: [0, -50, 50, 0] }}
            transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div
            style={{
              position: "absolute", bottom: "10%", right: "15%", width: "400px", height: "400px",
              background: "radial-gradient(circle, rgba(226, 59, 34, 0.3) 0%, rgba(0,0,0,0) 70%)",
              borderRadius: "50%", mixBlendMode: "screen", filter: "blur(60px)"
            }}
            animate={{ x: [0, -60, 40, 0], y: [0, 60, -40, 0] }}
            transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
          />
          <div style={{ position: "absolute", inset: 0, backgroundColor: "rgba(255,255,255,0.05)", backdropFilter: "blur(4px)" }} />
        </motion.div>

        {/* Footer Trees Overlay with gentle sway */}
        <motion.div 
          style={{ position: "fixed", bottom: -10, left: -20, right: -20, zIndex: -1, pointerEvents: "none", opacity: 0.95, mixBlendMode: "multiply", transformOrigin: "bottom center" }}
          animate={{ rotate: [-0.5, 0.5, -0.5] }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        >
          <img
            src="/assets/footer trees.png"
            alt="Footer Trees"
            style={{ width: "100%", objectFit: "cover", objectPosition: "bottom" }}
          />
        </motion.div>

        <Navbar />

        <BenchmarkRibbon data={benchData} />

        <div className={styles.gridContainer}>
          {children}
        </div>

        <footer className={styles.footer} style={{ position: "relative", zIndex: 10, display: "flex", justifyContent: "center", alignItems: "center", gap: "10px" }}>
          <span>Built for HH Goa 2026 · Powered by Sarvam AI saaras:v3 · FAISS Vector Engine · MSMARCO-XI</span>
          <img src="/assets/Hacker house.png" alt="Hacker House" style={{ height: "24px" }} />
        </footer>
      </div>
    </ReactLenis>
  );
}
