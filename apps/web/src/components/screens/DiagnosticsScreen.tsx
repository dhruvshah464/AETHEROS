'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { API_URL } from '@/lib/utils';

export function DiagnosticsScreen() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const load = () =>
      fetch(`${API_URL}/diagnostics/`)
        .then((r) => r.json())
        .then(setData)
        .catch(() => {});
    load();
    const i = setInterval(load, 3000);
    return () => clearInterval(i);
  }, []);

  const traces = (data?.recentTraces as Array<Record<string, unknown>>) || [];
  const failures = (data?.failures as Array<Record<string, unknown>>) || [];
  const heatmap = (data?.latencyHeatmap as Record<string, number[]>) || {};
  const eventEngine = data?.eventEngine as Record<string, number> | undefined;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      <HUDPanel title="Mission Diagnostics — NASA Control" delay={0.1}>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <Stat label="WebSockets" value={String(data?.websocketConnections ?? 0)} />
            <Stat label="Prometheus" value={data?.prometheus ? 'ONLINE' : 'OFFLINE'} />
            <Stat label="Events" value={String(eventEngine?.historySize ?? 0)} />
          </div>
          <div>
            <span className="hud-label">AI Latency Heatmap</span>
            <div className="mt-2 flex gap-1 h-24 items-end">
              {(heatmap.ai_inference || Array(24).fill(0)).map((v, i) => (
                <motion.div
                  key={i}
                  animate={{ height: `${Math.max(8, Math.min(100, v / 10))}%` }}
                  className="flex-1 bg-aether-cyan/40 rounded-t min-h-[4px]"
                />
              ))}
            </div>
          </div>
        </div>
      </HUDPanel>

      <HUDPanel title="Distributed Traces" delay={0.15}>
        <div className="p-4 max-h-[400px] overflow-y-auto space-y-2">
          {traces.map((t, i) => (
            <div key={i} className="p-2 border border-aether-border/20 font-mono text-[10px]">
              <div className="flex justify-between text-aether-cyan">
                <span>{String(t.name)}</span>
                <span className={t.status === 'ok' ? 'text-aether-green' : 'text-aether-red'}>
                  {Number(t.durationMs || 0).toFixed(0)}ms
                </span>
              </div>
            </div>
          ))}
          {traces.length === 0 && <p className="hud-label">Execute workflows to generate traces</p>}
        </div>
      </HUDPanel>

      <HUDPanel title="Failure Visualizer" className="lg:col-span-2" delay={0.2}>
        <div className="p-4 max-h-[200px] overflow-y-auto space-y-2">
          {failures.length === 0 ? (
            <p className="hud-label text-aether-green">All systems nominal</p>
          ) : (
            failures.map((f) => (
              <div key={String(f.id)} className="p-2 border border-aether-red/30 font-mono text-[10px] text-aether-red">
                [{String(f.subsystem)}] {String(f.error)}
              </div>
            ))
          )}
        </div>
      </HUDPanel>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 border border-aether-border/30 text-center">
      <span className="hud-label block">{label}</span>
      <span className="hud-value text-lg">{value}</span>
    </div>
  );
}
