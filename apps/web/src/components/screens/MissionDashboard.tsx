'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Plus } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { TerminalPanel } from '@/components/hud/TerminalPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

const STATUS_COLOR: Record<string, string> = {
  pending: '#00f0ff44',
  running: '#ffd700',
  complete: '#00ff88',
  failed: '#ff3366',
  waiting: '#7b61ff',
};

export function MissionDashboard() {
  const { activeWorkflow, workflows, updateWorkflow } = useAetherStore();
  const [running, setRunning] = useState(false);

  const launchDemoWorkflow = async () => {
    const res = await fetch(`${API_URL}/workflow/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: 'Recon Mission',
        nodes: [
          { id: 'n1', type: 'terminal', label: 'System Check', params: { command: 'echo AetherOS Mission Start' } },
          { id: 'n2', type: 'browser', label: 'Open Intel', params: { action: 'navigate', params: { url: 'https://github.com' }, force: true }, dependsOn: ['n1'] },
          { id: 'n3', type: 'ai', label: 'Analyze', params: { prompt: 'What is GitHub in one sentence?' }, dependsOn: ['n2'] },
        ],
      }),
    });
    const wf = await res.json();
    updateWorkflow(wf);
    useAetherStore.getState().setActiveWorkflow(wf);
    setRunning(true);
    await fetch(`${API_URL}/workflow/${wf.id}/execute`, { method: 'POST' });
    setRunning(false);
    const updated = await fetch(`${API_URL}/workflow/${wf.id}`);
    updateWorkflow(await updated.json());
  };

  const wf = activeWorkflow || workflows[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="Mission Workflow Graph" className="lg:col-span-2" delay={0.1}>
        <div className="p-6 min-h-[400px] relative">
          {!wf ? (
            <motion.div className="flex flex-col items-center justify-center h-64 gap-4">
              <p className="hud-label">No active mission — deploy a workflow</p>
              <button onClick={launchDemoWorkflow} className="hud-btn flex items-center gap-2">
                <Plus size={14} /> Deploy Recon Mission
              </button>
            </motion.div>
          ) : (
            <>
              <div className="flex justify-between mb-6">
                <div>
                  <h2 className="hud-text text-sm">{wf.name}</h2>
                  <span className="hud-label">Status: {wf.status}</span>
                </div>
                <button onClick={launchDemoWorkflow} disabled={running} className="hud-btn flex items-center gap-2">
                  <Play size={14} /> {running ? 'Executing...' : 'New Mission'}
                </button>
              </div>
              <div className="flex flex-wrap gap-8 justify-center">
                {wf.nodes.map((node, i) => (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="relative"
                  >
                    {i > 0 && (
                      <svg className="absolute -left-8 top-1/2 w-8 h-px" style={{ transform: 'translateY(-50%)' }}>
                        <line x1="0" y1="0" x2="32" y2="0" stroke="rgba(0,240,255,0.3)" strokeWidth="1" />
                      </svg>
                    )}
                    <div
                      className="w-28 h-28 border-2 flex flex-col items-center justify-center p-2"
                      style={{
                        borderColor: STATUS_COLOR[node.status] || STATUS_COLOR.pending,
                        boxShadow: `0 0 20px ${STATUS_COLOR[node.status] || STATUS_COLOR.pending}44`,
                      }}
                    >
                      <span className="font-mono text-[9px] text-aether-cyan uppercase">{node.type}</span>
                      <span className="font-mono text-[8px] text-aether-cyan/60 text-center mt-1">{node.label}</span>
                      <span className="hud-label text-[8px] mt-2" style={{ color: STATUS_COLOR[node.status] }}>
                        {node.status}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </div>
      </HUDPanel>
      <TerminalPanel />
    </div>
  );
}
