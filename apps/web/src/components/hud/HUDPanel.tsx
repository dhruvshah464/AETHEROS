'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface HUDPanelProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

export function HUDPanel({ title, children, className, delay = 0 }: HUDPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className={cn('hud-panel flex flex-col', className)}
    >
      {title && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-aether-border/50">
          <span className="hud-label">{title}</span>
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-aether-cyan animate-pulse-glow" />
            <span className="w-1.5 h-1.5 rounded-full bg-aether-cyan/30" />
          </div>
        </div>
      )}
      <motion.div className="flex-1 overflow-hidden">{children}</motion.div>
    </motion.div>
  );
}
