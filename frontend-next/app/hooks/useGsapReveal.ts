"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";

/**
 * A reusable hook that creates a coordinated GSAP timeline
 * for revealing child elements of a container.
 *
 * - Each direct child slides up and fades in with stagger
 * - Uses GSAP timeline for proper sequencing and cleanup
 * - Configurable delay, stagger, and easing
 */
export function useGsapReveal(options?: {
  delay?: number;
  stagger?: number;
  duration?: number;
  ease?: string;
  from?: "bottom" | "left" | "right" | "scale";
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tlRef = useRef<gsap.core.Timeline | null>(null);

  const {
    delay = 0.1,
    stagger = 0.12,
    duration = 0.7,
    ease = "power3.out",
    from = "bottom",
  } = options || {};

  useEffect(() => {
    const el = containerRef.current;
    if (!el || el.children.length === 0) return;

    // Kill any previous timeline
    if (tlRef.current) tlRef.current.kill();

    const children = Array.from(el.children);

    // Set initial hidden state immediately to prevent flash
    const fromVars: gsap.TweenVars = { opacity: 0 };
    if (from === "bottom") fromVars.y = 40;
    if (from === "left") fromVars.x = -40;
    if (from === "right") fromVars.x = 40;
    if (from === "scale") {
      fromVars.scale = 0.9;
      fromVars.y = 20;
    }

    gsap.set(children, fromVars);

    // Build a timeline
    const tl = gsap.timeline({ delay });
    tlRef.current = tl;

    const toVars: gsap.TweenVars = {
      opacity: 1,
      y: 0,
      x: 0,
      scale: 1,
      duration,
      stagger,
      ease,
      clearProps: "transform",
    };

    tl.to(children, toVars);

    return () => {
      tl.kill();
    };
  }, [delay, stagger, duration, ease, from]);

  return containerRef;
}

/**
 * A hook for animating a single element with GSAP on mount.
 * Great for hero sections, headings, and standalone elements.
 */
export function useGsapEntrance(options?: {
  delay?: number;
  duration?: number;
  y?: number;
  x?: number;
  scale?: number;
  rotation?: number;
  ease?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  const {
    delay = 0,
    duration = 0.8,
    y = 30,
    x = 0,
    scale = 1,
    rotation = 0,
    ease = "power3.out",
  } = options || {};

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    gsap.fromTo(
      el,
      { opacity: 0, y, x, scale: scale === 1 ? 0.95 : scale, rotation },
      {
        opacity: 1,
        y: 0,
        x: 0,
        scale: 1,
        rotation: 0,
        duration,
        delay,
        ease,
        clearProps: "transform",
      }
    );
  }, [delay, duration, y, x, scale, rotation, ease]);

  return ref;
}
