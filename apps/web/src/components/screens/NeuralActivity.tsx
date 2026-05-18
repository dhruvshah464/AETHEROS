'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';

export function NeuralActivity() {
  const { neuralTokens, aiStreaming, aiResponse, eventLog } = useAetherStore();

  useEffect(() => {
    if (!aiStreaming) return;
    const interval = setInterval(() => useAetherStore.getState().pushNeuralToken(), 200);
    return () => clearInterval(interval);
  }, [aiStreaming]);

  const aiEvents = eventLog.filter((e) => e.channel === 'ai').slice(0, 20);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      <HUDPanel title="Neural Token Flow" delay={0.1}>
        <div className="p-6">
          <div className="flex gap-1 h-40 items-end mb-6">
            {neuralTokens.map((h, i) => (
              <motion.div
                key={i}
                animate={{ height: `${Math.max(8, h)}%` }}
                transition={{ duration: 0.3 }}
                className="flex-1 rounded-t-sm"
                style={{
                  background: `linear-gradient(to top, rgba(0,240,255,0.2), rgba(0,240,255,${0.3 + h / 200}))`,
                  boxShadow: h > 50 ? '0 0 10px #00f0ff' : 'none',
                }}
              />
            ))}
          </div>
          <div className="relative h-32 border border-aether-cyan/10 overflow-hidden">
            {Array.from({ length: 8 }).map((_, row) => (
              <div key={row} className="flex">
                {Array.from({ length: 16 }).map((_, col) => (
                  <motion.div
                    key={col}
                    animate={{ opacity: [0.1, Math.random() * 0.8, 0.1] }}
                    transition={{ repeat: Infinity, duration: 1 + Math.random(), delay: col * 0.05 }}
                    className="w-6 h-6 border border-aether-cyan/5"
                    style={{
                      background: `rgba(123, 97, 255, ${Math.random() * 0.3})`,
                    }}
                  />
                ))}
              </div>
            ))}
            <span className="absolute bottom-2 right-2 hud-label">Attention Heatmap</span>
          </div>
        </div>
      </HUDPanel>

      <HUDPanel title="Inference Stream" delay={0.15}>
        <div className="p-4 space-y-2 max-h-[500px] overflow-y-auto">
          {aiResponse && (
            <motion.div className="p-3 border border-aether-purple/30 font-mono text-xs text-aether-cyan/80">
              {aiResponse.slice(-500)}
            </motion.div>
          )}
          {aiEvents.map((e) => (
            <div key={e.id} className="flex gap-2 font-mono text-[10px] text-aether-cyan/40">
              <span className="text-aether-purple">{e.type}</span>
              <span>{new Date(e.timestamp).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </HUDPanel>
    </div>
  );
}
