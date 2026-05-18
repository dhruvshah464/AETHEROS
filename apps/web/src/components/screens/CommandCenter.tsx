'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Sparkles } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';

interface CommandCenterProps {
  onSend: (prompt: string) => void;
}

const QUICK_COMMANDS = [
  'Analyze system status',
  'Deploy research agent',
  'Scan environment',
  'Initialize security audit',
  'Show agent network',
];

export function CommandCenter({ onSend }: CommandCenterProps) {
  const [input, setInput] = useState('');
  const { aiResponse, aiStreaming, aiThoughts } = useAetherStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [aiResponse]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || aiStreaming) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="AETHER — Command Interface" className="lg:col-span-2 h-full" delay={0.1}>
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[calc(100vh-280px)]">
          {!aiResponse && !aiStreaming && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-48 gap-4"
            >
              <Sparkles className="w-8 h-8 text-aether-cyan/30" />
              <p className="hud-label text-center">
                AETHER Intelligence Online — Awaiting Command
              </p>
            </motion.div>
          )}

          <AnimatePresence>
            {aiStreaming && !aiResponse && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-2 items-center"
              >
                <span className="hud-label">Processing</span>
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                    className="w-1.5 h-1.5 bg-aether-cyan rounded-full"
                  />
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {aiResponse && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="font-mono text-sm leading-relaxed text-aether-cyan/90 whitespace-pre-wrap"
            >
              {aiResponse}
              {aiStreaming && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ repeat: Infinity, duration: 0.8 }}
                  className="inline-block w-2 h-4 bg-aether-cyan ml-1 align-middle"
                />
              )}
            </motion.div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="p-4 border-t border-aether-border/30">
          <motion.div className="flex gap-2">
            <input
              className="hud-input flex-1"
              placeholder="Enter command for AETHER..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={aiStreaming}
            />
            <button type="submit" className="hud-btn flex items-center gap-2" disabled={aiStreaming}>
              <Send size={14} />
              Execute
            </button>
          </motion.div>
          <div className="flex flex-wrap gap-2 mt-3">
            {QUICK_COMMANDS.map((cmd) => (
              <button
                key={cmd}
                type="button"
                onClick={() => onSend(cmd)}
                className="hud-label px-2 py-1 border border-aether-border/30 hover:border-aether-cyan/50 hover:text-aether-cyan transition-colors cursor-pointer"
              >
                {cmd}
              </button>
            ))}
          </div>
        </form>
      </HUDPanel>

      <HUDPanel title="Reasoning Stream" className="h-full" delay={0.2}>
        <div className="p-4 space-y-3 overflow-y-auto max-h-[calc(100vh-200px)]">
          {aiThoughts.length === 0 ? (
            <p className="hud-label">Thought graph will appear during complex operations</p>
          ) : (
            aiThoughts.map((thought, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="border-l-2 border-aether-purple/50 pl-3"
              >
                <span className="hud-label text-aether-purple">{thought.type}</span>
                <p className="font-mono text-xs text-aether-cyan/70 mt-1">{thought.content}</p>
              </motion.div>
            ))
          )}

          {aiStreaming && (
            <motion.div
              animate={{ opacity: [0.3, 1, 0.3] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="mt-4 p-3 border border-aether-cyan/20"
            >
              <span className="hud-label">Neural activity detected</span>
              <motion.div className="mt-2 flex gap-1 h-8 items-end">
                {Array.from({ length: 12 }).map((_, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: ['20%', `${30 + Math.random() * 70}%`, '20%'] }}
                    transition={{ repeat: Infinity, duration: 0.5 + Math.random(), delay: i * 0.05 }}
                    className="flex-1 bg-aether-cyan/40 rounded-sm"
                  />
                ))}
              </motion.div>
            </motion.div>
          )}
        </div>
      </HUDPanel>
    </div>
  );
}
