'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Star } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { API_URL } from '@/lib/utils';

interface PluginCard {
  id: string;
  name: string;
  description?: string;
  version?: string;
  author?: string;
  rating?: number;
  installs?: number;
  status?: string;
}

export function PluginMarketplace() {
  const [plugins, setPlugins] = useState<PluginCard[]>([]);

  useEffect(() => {
    fetch(`${API_URL}/plugins/marketplace`)
      .then((r) => r.json())
      .then((d) => setPlugins(d.plugins || []))
      .catch(() => {});
  }, []);

  const install = async () => {
    await fetch(`${API_URL}/plugins/discover`, { method: 'POST' });
  };

  return (
    <HUDPanel title="Plugin Marketplace" delay={0.1}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <p className="hud-label">Extensible like VSCode — agents, tools, workflows</p>
          <button onClick={install} className="hud-btn flex items-center gap-2">
            <Download size={14} /> Refresh Registry
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[calc(100vh-220px)] overflow-y-auto">
          {plugins.map((p, i) => (
            <motion.div
              key={p.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="p-4 border border-aether-border/30 hud-panel hover:border-aether-cyan/50 transition-colors"
            >
              <div className="flex justify-between items-start">
                <span className="hud-text text-xs">{p.name}</span>
                {p.status === 'installed' && (
                  <span className="text-[9px] text-aether-green font-mono">INSTALLED</span>
                )}
              </div>
              <p className="font-mono text-[10px] text-aether-cyan/50 mt-2 line-clamp-2">
                {p.description || 'AetherOS extension'}
              </p>
              <div className="flex gap-3 mt-3 hud-label text-[9px]">
                <span className="flex items-center gap-1">
                  <Star size={10} className="text-aether-gold" />
                  {p.rating?.toFixed(1) ?? '5.0'}
                </span>
                <span>{p.installs ?? 0} installs</span>
                <span>v{p.version || '1.0'}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </HUDPanel>
  );
}
