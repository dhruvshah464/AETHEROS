'use client';

import { motion } from 'framer-motion';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';

function Gauge({ label, value, max = 100, color = '#00f0ff' }: { label: string; value: number; max?: number; color?: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between hud-label">
        <span>{label}</span>
        <span className="hud-value">{value.toFixed(1)}%</span>
      </div>
      <div className="h-1.5 bg-aether-cyan/10 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5 }}
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}44, ${color})`, boxShadow: `0 0 8px ${color}66` }}
        />
      </div>
    </div>
  );
}

function RadarDisplay() {
  return (
    <div className="relative w-40 h-40 mx-auto">
      {[1, 0.66, 0.33].map((scale, i) => (
        <div
          key={i}
          className="absolute inset-0 rounded-full border border-aether-cyan/20"
          style={{ transform: `scale(${scale})` }}
        />
      ))}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}
        className="absolute inset-0 origin-center"
      >
        <motion.div
          className="absolute top-1/2 left-1/2 w-1/2 h-0.5 origin-left"
          style={{
            background: 'linear-gradient(90deg, rgba(0,240,255,0.8), transparent)',
            transform: 'translateY(-50%)',
          }}
        />
      </motion.div>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="hud-label">SCAN</span>
      </div>
    </div>
  );
}

export function TelemetryScreen() {
  const { telemetry } = useAetherStore();
  const t = telemetry;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="System Core" delay={0.1}>
        <div className="p-4 space-y-4">
          <Gauge label="CPU" value={t?.cpu?.percent ?? 0} />
          <Gauge label="Memory" value={t?.memory?.percent ?? 0} color="#7b61ff" />
          <Gauge label="Disk" value={t?.disk?.percent ?? 0} color="#00ff88" />
          <div className="grid grid-cols-2 gap-4 pt-2">
            <div>
              <span className="hud-label">Cores</span>
              <p className="hud-value text-xl">{t?.cpu?.cores ?? '—'}</p>
            </div>
            <motion.div>
              <span className="hud-label">Freq</span>
              <p className="hud-value text-xl">{t?.cpu?.freqMhz ? `${t.cpu.freqMhz} MHz` : '—'}</p>
            </motion.div>
          </div>
        </div>
      </HUDPanel>

      <HUDPanel title="Radar — Process Scan" delay={0.15}>
        <div className="p-4 flex flex-col items-center gap-4">
          <RadarDisplay />
          <div className="w-full space-y-1 max-h-32 overflow-y-auto">
            {(t?.processes ?? []).slice(0, 6).map((p) => (
              <div key={p.pid} className="flex justify-between font-mono text-[10px] text-aether-cyan/60">
                <span className="truncate max-w-[120px]">{p.name}</span>
                <span>{p.cpuPercent}%</span>
              </div>
            ))}
          </div>
        </div>
      </HUDPanel>

      <HUDPanel title="GPU / AI Usage" delay={0.2}>
        <div className="p-4 space-y-4">
          {t?.gpu && t.gpu.length > 0 ? (
            t.gpu.map((g, i) => (
              <div key={i} className="space-y-2">
                <span className="hud-label truncate block">{g.name}</span>
                <Gauge label="GPU Util" value={g.utilization} color="#ffd700" />
                <div className="flex justify-between hud-label">
                  <span>VRAM</span>
                  <span>{g.memoryUsedMb.toFixed(0)} / {g.memoryTotalMb.toFixed(0)} MB</span>
                </div>
              </div>
            ))
          ) : (
            <p className="hud-label">No GPU detected — CPU inference mode</p>
          )}
          <div className="border-t border-aether-border/30 pt-4 space-y-2">
            <span className="hud-label">AI Token Usage</span>
            <motion.div className="grid grid-cols-2 gap-2">
              <div>
                <span className="hud-label">In</span>
                <p className="hud-value">{t?.aiUsage?.tokensIn ?? 0}</p>
              </div>
              <div>
                <span className="hud-label">Out</span>
                <p className="hud-value">{t?.aiUsage?.tokensOut ?? 0}</p>
              </div>
            </motion.div>
            <p className="hud-label">
              Latency: {t?.aiUsage?.inferenceLatencyMs?.toFixed(0) ?? 0}ms
            </p>
          </div>
        </div>
      </HUDPanel>
    </div>
  );
}
