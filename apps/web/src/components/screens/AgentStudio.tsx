'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Layers } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { API_URL } from '@/lib/utils';

interface Template {
  id: string;
  name: string;
  description: string;
  nodes: unknown[];
}

export function AgentStudio() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [deploying, setDeploying] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/studio/templates`)
      .then((r) => r.json())
      .then((d) => setTemplates(d.templates || []))
      .catch(() => {});
  }, []);

  const deploy = async (id: string) => {
    setDeploying(id);
    await fetch(`${API_URL}/studio/deploy/${id}`, { method: 'POST' });
    setDeploying(null);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="Agent Studio — Visual Workflow Builder" className="lg:col-span-2" delay={0.1}>
        <div className="p-6 min-h-[400px] relative">
          <div className="absolute inset-0 grid-bg opacity-30" />
          <div className="relative flex flex-wrap gap-6 justify-center items-center min-h-[300px]">
            {['Input', 'AI Agent', 'Browser', 'Terminal', 'Output'].map((node, i) => (
              <motion.div
                key={node}
                drag
                dragConstraints={{ left: -200, right: 200, top: -100, bottom: 100 }}
                className="w-24 h-24 border-2 border-aether-cyan/40 flex flex-col items-center justify-center cursor-grab active:cursor-grabbing bg-black/60"
                whileHover={{ scale: 1.05, boxShadow: '0 0 20px rgba(0,240,255,0.3)' }}
              >
                <Layers size={16} className="text-aether-cyan mb-1" />
                <span className="font-mono text-[8px] text-aether-cyan">{node}</span>
              </motion.div>
            ))}
          </div>
          <p className="hud-label text-center mt-4 relative">Drag nodes to design — deploy templates from the panel</p>
        </div>
      </HUDPanel>

      <HUDPanel title="Workflow Templates" delay={0.15}>
        <div className="p-4 space-y-3 max-h-[500px] overflow-y-auto">
          {templates.map((t) => (
            <div key={t.id} className="p-3 border border-aether-border/20">
              <span className="hud-text text-xs">{t.name}</span>
              <p className="font-mono text-[10px] text-aether-cyan/50 mt-1">{t.description}</p>
              <button
                onClick={() => deploy(t.id)}
                disabled={deploying === t.id}
                className="hud-btn mt-2 w-full flex items-center justify-center gap-2 text-[10px]"
              >
                <Play size={12} />
                {deploying === t.id ? 'Deploying...' : 'Deploy'}
              </button>
            </div>
          ))}
        </div>
      </HUDPanel>
    </div>
  );
}
