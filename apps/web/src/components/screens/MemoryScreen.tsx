'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { API_URL } from '@/lib/utils';
import { useAetherStore } from '@/store/aether-store';

export function MemoryScreen() {
  const { memories } = useAetherStore();
  const [timeline, setTimeline] = useState<Array<{ id: string; content: string; metadata?: Record<string, unknown> }>>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<typeof timeline>([]);
  const [graphNodes, setGraphNodes] = useState<Array<{ id: string; content: string; importance?: number }>>([]);

  useEffect(() => {
    fetch(`${API_URL}/ai/memory/timeline`)
      .then((r) => r.json())
      .then((d) => setTimeline(d.entries || []))
      .catch(() => {});
    fetch(`${API_URL}/memory/v3/graph`)
      .then((r) => r.json())
      .then((d) => setGraphNodes(d.nodes || []))
      .catch(() => {});
  }, [memories]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    const res = await fetch(`${API_URL}/memory/v3/search?q=${encodeURIComponent(searchQuery)}`);
    const data = await res.json();
    setSearchResults(data.nodes || []);
    setGraphNodes(data.nodes || []);
  };

  const entries = searchResults.length > 0 ? searchResults : timeline.length > 0 ? timeline : memories;

  return (
    <HUDPanel title="Memory V3 — Neural Knowledge Graph" delay={0.1}>
      <div className="p-4">
        {graphNodes.length > 0 && (
          <div className="mb-6 p-4 border border-aether-purple/20 min-h-[120px] relative">
            <span className="hud-label text-aether-purple">Knowledge Graph</span>
            <div className="flex flex-wrap gap-2 mt-3 justify-center">
              {graphNodes.slice(0, 12).map((n, i) => (
                <motion.div
                  key={n.id}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="w-16 h-16 rounded-full border border-aether-cyan/40 flex items-center justify-center p-1"
                  style={{
                    boxShadow: `0 0 ${(n.importance || 0.5) * 20}px rgba(0,240,255,0.4)`,
                  }}
                >
                  <span className="font-mono text-[7px] text-center text-aether-cyan/70 line-clamp-3">
                    {n.content.slice(0, 40)}
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
        )}
        <div className="flex gap-2 mb-6">
          <input
            className="hud-input flex-1"
            placeholder="Semantic memory search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} className="hud-btn">
            Recall
          </button>
        </div>

        <div className="relative pl-6 space-y-4 max-h-[calc(100vh-280px)] overflow-y-auto">
          <div className="absolute left-2 top-0 bottom-0 w-px bg-aether-cyan/20" />
          {entries.length === 0 ? (
            <p className="hud-label">No memories stored yet — interact with AETHER to build memory</p>
          ) : (
            entries.map((entry, i) => (
              <motion.div
                key={entry.id || i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="relative"
              >
                <div className="absolute -left-4 w-2 h-2 rounded-full bg-aether-cyan border border-aether-cyan" />
                <div className="p-3 border border-aether-border/20 bg-aether-panel">
                  <p className="font-mono text-xs text-aether-cyan/80">{entry.content}</p>
                  {entry.metadata && (
                    <span className="hud-label mt-2 block">
                      {(entry.metadata as { type?: string }).type || 'episodic'}
                    </span>
                  )}
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </HUDPanel>
  );
}
