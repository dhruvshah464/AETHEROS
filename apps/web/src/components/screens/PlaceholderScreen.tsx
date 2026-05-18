'use client';

import { motion } from 'framer-motion';
import { HUDPanel } from '@/components/hud/HUDPanel';

interface PlaceholderScreenProps {
  title: string;
  description: string;
  features: string[];
}

export function PlaceholderScreen({ title, description, features }: PlaceholderScreenProps) {
  return (
    <HUDPanel title={title} delay={0.1}>
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-6">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
          className="w-24 h-24 border border-aether-cyan/30 rounded-full flex items-center justify-center"
        >
          <div className="w-16 h-16 border border-aether-cyan/50 rounded-full" />
        </motion.div>
        <p className="hud-label text-center max-w-md">{description}</p>
        <ul className="space-y-2">
          {features.map((f, i) => (
            <motion.li
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="font-mono text-xs text-aether-cyan/50 flex items-center gap-2"
            >
              <span className="text-aether-cyan">◆</span> {f}
            </motion.li>
          ))}
        </ul>
        <span className="hud-label text-aether-cyan/30">Phase 4 — In Development</span>
      </div>
    </HUDPanel>
  );
}
