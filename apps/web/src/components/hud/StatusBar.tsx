'use client';

import { motion } from 'framer-motion';
import { Rocket } from 'lucide-react';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

export function StatusBar() {
  const { connected, telemetry, aiStreaming, demoRunning, demoStep, setActiveScreen } = useAetherStore();

  const time = new Date().toLocaleTimeString('en-US', { hour12: false });
  const cpu = telemetry?.cpu?.percent ?? 0;
  const mem = telemetry?.memory?.percent ?? 0;

  return (
    <motion.header
      initial={{ y: -10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="flex items-center justify-between px-6 py-2 border-b border-aether-border/30 bg-black/30 backdrop-blur-sm"
    >
      <motion.div className="flex items-center gap-6">
        <h1 className="hud-text text-lg font-bold tracking-[0.3em]">
          AETHER<span className="text-aether-cyan/50">OS</span>
        </h1>
        <span className="hud-label hidden md:inline">v0.3.0 — Platform Edition</span>
      </motion.div>

      <div className="flex items-center gap-8">
        {demoRunning && demoStep && (
          <motion.span
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
            className="hud-label text-aether-gold max-w-[180px] truncate"
          >
            ◆ {demoStep}
          </motion.span>
        )}

        <button
          onClick={async () => {
            if (demoRunning) {
              await fetch(`${API_URL}/demo/stop`, { method: 'POST' });
              return;
            }
            setActiveScreen('browser');
            await fetch(`${API_URL}/demo/start`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ sequence: 'mission_impossible' }),
            });
          }}
          className={`hud-btn flex items-center gap-2 !py-1 !px-3 text-[10px] ${
            demoRunning ? 'border-aether-gold text-aether-gold' : ''
          }`}
        >
          <Rocket size={12} />
          {demoRunning ? 'Stop Demo' : 'Launch Demo'}
        </button>

        {aiStreaming && (
          <motion.span
            animate={{ opacity: [1, 0.4, 1] }}
            transition={{ repeat: Infinity, duration: 1 }}
            className="hud-label text-aether-green"
          >
            ◆ NEURAL STREAM ACTIVE
          </motion.span>
        )}

        <div className="flex gap-4 hud-label">
          <span>CPU {cpu.toFixed(0)}%</span>
          <span>MEM {mem.toFixed(0)}%</span>
        </div>

        <div className="flex items-center gap-2">
          <motion.span
            animate={{ scale: connected ? [1, 1.2, 1] : 1 }}
            transition={{ repeat: connected ? Infinity : 0, duration: 2 }}
            className={`w-2 h-2 rounded-full ${connected ? 'bg-aether-green shadow-[0_0_8px_#00ff88]' : 'bg-aether-red'}`}
          />
          <span className="hud-label">{connected ? 'ONLINE' : 'OFFLINE'}</span>
        </div>

        <span className="hud-value font-mono text-xs">{time}</span>
      </div>
    </motion.header>
  );
}
