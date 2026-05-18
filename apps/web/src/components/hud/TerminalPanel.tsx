'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Terminal } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

export function TerminalPanel() {
  const { terminalOutput, clearTerminalOutput } = useAetherStore();
  const [cmd, setCmd] = useState('echo AetherOS Terminal Online');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [terminalOutput]);

  const execute = async () => {
    clearTerminalOutput();
    await fetch(`${API_URL}/terminal/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd }),
    });
  };

  return (
    <HUDPanel title="Terminal — Sandboxed" delay={0.15}>
      <div className="flex flex-col h-full min-h-[300px]">
        <div
          ref={scrollRef}
          className="flex-1 p-3 font-mono text-xs text-aether-green/90 bg-black/60 overflow-y-auto max-h-[280px]"
          style={{ textShadow: '0 0 8px rgba(0,255,136,0.3)' }}
        >
          {terminalOutput || (
            <span className="text-aether-cyan/30"># AetherOS sandbox ready — allowed commands only</span>
          )}
          <motion.span
            animate={{ opacity: [1, 0] }}
            transition={{ repeat: Infinity, duration: 0.8 }}
            className="inline-block w-2 h-4 bg-aether-green ml-1 align-middle"
          />
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            execute();
          }}
          className="flex gap-2 p-3 border-t border-aether-border/30"
        >
          <span className="text-aether-green font-mono">$</span>
          <input
            className="hud-input flex-1 text-aether-green border-aether-green/20"
            value={cmd}
            onChange={(e) => setCmd(e.target.value)}
          />
          <button type="submit" className="hud-btn flex items-center gap-1">
            <Terminal size={12} /> Run
          </button>
        </form>
      </div>
    </HUDPanel>
  );
}
