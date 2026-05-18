'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Globe, Play, Shield, Zap, Check, X } from 'lucide-react';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

export function BrowserControl() {
  const {
    browserScreenshot,
    browserUrl,
    browserActions,
    browserMode,
    pendingApproval,
    setBrowserMode,
    setBrowserStreaming,
    setPendingApproval,
  } = useAetherStore();
  const [urlInput, setUrlInput] = useState('https://news.ycombinator.com');
  const [launched, setLaunched] = useState(false);

  const launch = async () => {
    const res = await fetch(`${API_URL}/browser/launch`, { method: 'POST' });
    const data = await res.json();
    setLaunched(data.active);
    setBrowserStreaming(true);
  };

  const runAction = async (action: string, params: Record<string, unknown> = {}, force = false) => {
    await fetch(`${API_URL}/browser/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, params, force }),
    });
  };

  const approve = async () => {
    if (!pendingApproval) return;
    await fetch(`${API_URL}/browser/approve/${pendingApproval.id}`, { method: 'POST' });
    setPendingApproval(null);
  };

  const setMode = async (mode: string) => {
    await fetch(`${API_URL}/browser/mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    });
    setBrowserMode(mode);
  };

  useEffect(() => {
    if (!launched) return;
    const poll = setInterval(async () => {
      const res = await fetch(`${API_URL}/browser/state`);
      const data = await res.json();
      if (data.url) useAetherStore.getState().setBrowserUrl(data.url);
    }, 5000);
    return () => clearInterval(poll);
  }, [launched]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="Autonomous Browser — Live Feed" className="lg:col-span-2" delay={0.1}>
        <div className="p-4 flex flex-col gap-4 h-full">
          <div className="relative aspect-video bg-black/80 border border-aether-cyan/20 overflow-hidden">
            {browserScreenshot ? (
              <img
                src={`data:image/png;base64,${browserScreenshot}`}
                alt="Browser viewport"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <Globe className="w-16 h-16 text-aether-cyan/20" />
              </div>
            )}
            <div className="absolute inset-0 pointer-events-none">
              <motion.div className="absolute top-3 left-3 w-10 h-10 border-t-2 border-l-2 border-aether-cyan/60" />
              <motion.div className="absolute top-3 right-3 w-10 h-10 border-t-2 border-r-2 border-aether-cyan/60" />
              <motion.div className="absolute bottom-3 left-3 w-10 h-10 border-b-2 border-l-2 border-aether-cyan/60" />
              <motion.div className="absolute bottom-3 right-3 w-10 h-10 border-b-2 border-r-2 border-aether-cyan/60" />
              <motion.div
                animate={{ top: ['0%', '100%', '0%'] }}
                transition={{ repeat: Infinity, duration: 4, ease: 'linear' }}
                className="absolute left-0 right-0 h-px bg-aether-cyan/40"
              />
            </div>
            {browserUrl && (
              <div className="absolute bottom-0 left-0 right-0 bg-black/80 px-3 py-1 font-mono text-[10px] text-aether-cyan/70 truncate">
                {browserUrl}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            {!launched ? (
              <button onClick={launch} className="hud-btn flex items-center gap-2">
                <Play size={14} /> Launch Browser
              </button>
            ) : (
              <>
                <input
                  className="hud-input flex-1 min-w-[200px]"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="URL"
                />
                <button onClick={() => runAction('navigate', { url: urlInput })} className="hud-btn">
                  Navigate
                </button>
                <button onClick={() => runAction('search', { query: 'AetherOS AI' })} className="hud-btn">
                  Search
                </button>
                <button onClick={() => runAction('screenshot', {})} className="hud-btn">
                  Capture
                </button>
              </>
            )}
            <button
              onClick={() => setMode(browserMode === 'safe' ? 'autonomous' : 'safe')}
              className={`hud-btn flex items-center gap-2 ${browserMode === 'autonomous' ? 'border-aether-green text-aether-green' : ''}`}
            >
              {browserMode === 'safe' ? <Shield size={14} /> : <Zap size={14} />}
              {browserMode === 'safe' ? 'Safe' : 'Autonomous'}
            </button>
          </div>
        </div>
      </HUDPanel>

      <div className="flex flex-col gap-4">
        <AnimatePresence>
          {pendingApproval && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="hud-panel p-4 border-aether-gold/50"
            >
              <span className="hud-label text-aether-gold">Approval Required</span>
              <p className="font-mono text-xs text-aether-cyan/80 mt-2">{pendingApproval.description}</p>
              <div className="flex gap-2 mt-3">
                <button onClick={approve} className="hud-btn flex items-center gap-1 text-aether-green border-aether-green/50">
                  <Check size={14} /> Approve
                </button>
                <button onClick={() => setPendingApproval(null)} className="hud-btn flex items-center gap-1">
                  <X size={14} /> Deny
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <HUDPanel title="Action Stream" delay={0.15}>
          <div className="p-3 space-y-2 max-h-[400px] overflow-y-auto">
            {browserActions.length === 0 ? (
              <p className="hud-label">No actions yet</p>
            ) : (
              browserActions.map((a) => (
                <div key={a.id} className="p-2 border border-aether-border/20 font-mono text-[10px]">
                  <div className="flex justify-between">
                    <span className="text-aether-cyan uppercase">{a.type}</span>
                    <span
                      className={
                        a.status === 'complete'
                          ? 'text-aether-green'
                          : a.status === 'failed'
                            ? 'text-aether-red'
                            : 'text-aether-gold'
                      }
                    >
                      {a.status}
                    </span>
                  </div>
                  <p className="text-aether-cyan/50 mt-1">{a.description}</p>
                </div>
              ))
            )}
          </div>
        </HUDPanel>
      </div>
    </div>
  );
}
