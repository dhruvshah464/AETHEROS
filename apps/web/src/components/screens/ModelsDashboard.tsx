'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Zap } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

export function ModelsDashboard() {
  const { models, providers, telemetry } = useAetherStore();
  const [benchmark, setBenchmark] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/models/`)
      .then((r) => r.json())
      .then((d) => useAetherStore.getState().setModels({ models: d.models || [], providers: d.providers || [] }))
      .catch(() => {});
  }, []);

  const runBenchmark = async (provider: string) => {
    setLoading(true);
    const res = await fetch(`${API_URL}/models/benchmark`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider }),
    });
    setBenchmark(await res.json());
    setLoading(false);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="Neural Compute — Providers" className="lg:col-span-2" delay={0.1}>
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map((p) => (
            <motion.div
              key={p.name}
              whileHover={{ scale: 1.02 }}
              className="p-4 border border-aether-border/30 hud-panel"
            >
              <div className="flex items-center justify-between">
                <span className="hud-text text-xs">{p.name.toUpperCase()}</span>
                <span
                  className={`hud-label ${p.status === 'online' || p.status === 'configured' ? 'text-aether-green' : 'text-aether-red'}`}
                >
                  {p.status}
                </span>
              </div>
              <button
                onClick={() => runBenchmark(p.name)}
                disabled={loading}
                className="hud-btn mt-3 text-[10px] flex items-center gap-1"
              >
                <Zap size={12} /> Benchmark
              </button>
            </motion.div>
          ))}
          {benchmark && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="col-span-full p-3 border border-aether-cyan/30 font-mono text-xs text-aether-cyan"
            >
              {JSON.stringify(benchmark, null, 2)}
            </motion.div>
          )}
        </div>
      </HUDPanel>

      <HUDPanel title="Local Models — Ollama" delay={0.15}>
        <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
          {models.length === 0 ? (
            <p className="hud-label">No local models — start Ollama</p>
          ) : (
            models.map((m) => (
              <div key={m.id} className="p-3 border border-aether-border/20">
                <div className="flex items-center gap-2">
                  <Cpu size={14} className="text-aether-cyan" />
                  <span className="font-mono text-xs text-aether-cyan">{m.id}</span>
                </div>
                <span className="hud-label">{m.provider}</span>
              </div>
            ))
          )}
          <div className="pt-4 border-t border-aether-border/30">
            <span className="hud-label">Token Usage</span>
            <p className="hud-value">In: {telemetry?.aiUsage?.tokensIn ?? 0}</p>
            <p className="hud-value">Out: {telemetry?.aiUsage?.tokensOut ?? 0}</p>
            <p className="hud-label mt-2">
              Latency: {telemetry?.aiUsage?.inferenceLatencyMs?.toFixed(0) ?? 0}ms
            </p>
          </div>
        </div>
      </HUDPanel>
    </div>
  );
}
