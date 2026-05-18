'use client';

import { motion } from 'framer-motion';

/** Cinematic FUI overlay — scanlines, vignette, energy pulse (GPU-friendly CSS). */
export function FUIShader() {
  return (
    <div className="pointer-events-none fixed inset-0 z-[5]" aria-hidden>
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 240, 255, 0.4) 2px,
            rgba(0, 240, 255, 0.4) 4px
          )`,
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 35%, rgba(0,0,0,0.65) 100%)',
        }}
      />
      <motion.div
        animate={{ opacity: [0.02, 0.08, 0.02] }}
        transition={{ repeat: Infinity, duration: 5, ease: 'easeInOut' }}
        className="absolute inset-0 bg-gradient-to-tr from-cyan-500/5 via-transparent to-purple-500/5"
      />
    </div>
  );
}
