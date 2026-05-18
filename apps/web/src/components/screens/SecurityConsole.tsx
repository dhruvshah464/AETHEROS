'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Unlock } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { API_URL } from '@/lib/utils';

export function SecurityConsole() {
  const [mode, setMode] = useState('safe');
  const [audit, setAudit] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    fetch(`${API_URL}/auth/bootstrap`)
      .then((r) => r.json())
      .then((d) => setMode(d.executionMode || 'safe'))
      .catch(() => {});
    fetch(`${API_URL}/auth/audit`)
      .then((r) => r.json())
      .then((d) => setAudit(d.entries || []))
      .catch(() => {});
  }, []);

  const setExecutionMode = async (m: string) => {
    await fetch(`${API_URL}/auth/mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: m }),
    });
    setMode(m);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
      <HUDPanel title="Security Runtime" delay={0.1}>
        <div className="p-6 space-y-6">
          <p className="hud-label">Execution Mode</p>
          <div className="flex flex-wrap gap-3">
            {[
              { id: 'safe', label: 'Safe', icon: Shield, desc: 'Approval required for risky actions' },
              { id: 'developer', label: 'Developer', icon: Unlock, desc: 'Full tool access with audit' },
              { id: 'airgapped', label: 'Air-Gapped', icon: Lock, desc: 'No external browser/terminal' },
            ].map(({ id, label, icon: Icon, desc }) => (
              <button
                key={id}
                onClick={() => setExecutionMode(id)}
                className={`flex-1 min-w-[140px] p-4 border text-left transition-all ${
                  mode === id ? 'border-aether-cyan bg-aether-cyan/10 shadow-hud' : 'border-aether-border/30'
                }`}
              >
                <Icon size={20} className="text-aether-cyan mb-2" />
                <span className="hud-text text-xs block">{label}</span>
                <span className="font-mono text-[9px] text-aether-cyan/50 mt-1 block">{desc}</span>
              </button>
            ))}
          </div>
          <div className="p-4 border border-aether-border/20">
            <span className="hud-label">RBAC Roles</span>
            <p className="font-mono text-xs text-aether-cyan/70 mt-2">viewer → operator → admin</p>
            <p className="font-mono text-[10px] text-aether-cyan/40 mt-1">
              API keys & JWT via /auth/token — audit log below
            </p>
          </div>
        </div>
      </HUDPanel>

      <HUDPanel title="Audit Log — Risk Scoring" delay={0.15}>
        <div className="p-4 max-h-[450px] overflow-y-auto space-y-2">
          {audit.map((e) => (
            <motion.div
              key={String(e.id)}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              className={`p-2 border font-mono text-[10px] ${
                e.allowed ? 'border-aether-green/30' : 'border-aether-red/30'
              }`}
            >
              <div className="flex justify-between">
                <span className="text-aether-cyan">{String(e.action)}</span>
                <span className={e.allowed ? 'text-aether-green' : 'text-aether-red'}>
                  risk {(Number(e.riskScore) * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-aether-cyan/50 mt-1 truncate">{String(e.detail)}</p>
            </motion.div>
          ))}
          {audit.length === 0 && <p className="hud-label">No audit entries yet</p>}
        </div>
      </HUDPanel>
    </div>
  );
}
