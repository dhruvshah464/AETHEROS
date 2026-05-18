'use client';

import { motion } from 'framer-motion';
import {
  Brain,
  Eye,
  Network,
  Activity,
  Database,
  Globe,
  Mic,
  Target,
  Zap,
  Cpu,
  Shield,
  ActivitySquare,
  Puzzle,
  Wand2,
} from 'lucide-react';
import type { ScreenId } from '@aetheros/types';
import { useAetherStore } from '@/store/aether-store';
import { cn } from '@/lib/utils';

const NAV_ITEMS: { id: ScreenId; label: string; icon: typeof Brain }[] = [
  { id: 'command', label: 'Command', icon: Brain },
  { id: 'vision', label: 'Vision', icon: Eye },
  { id: 'agents', label: 'Agents', icon: Network },
  { id: 'telemetry', label: 'Telemetry', icon: Activity },
  { id: 'memory', label: 'Memory', icon: Database },
  { id: 'browser', label: 'Browser', icon: Globe },
  { id: 'voice', label: 'Voice', icon: Mic },
  { id: 'mission', label: 'Mission', icon: Target },
  { id: 'neural', label: 'Neural', icon: Zap },
  { id: 'models', label: 'Models', icon: Cpu },
  { id: 'diagnostics', label: 'Diagnostics', icon: ActivitySquare },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'studio', label: 'Studio', icon: Wand2 },
  { id: 'marketplace', label: 'Plugins', icon: Puzzle },
];

export function Sidebar() {
  const { activeScreen, setActiveScreen, connected } = useAetherStore();

  return (
    <motion.nav
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="flex flex-col w-16 h-full border-r border-aether-border/30 bg-black/40 backdrop-blur-sm"
    >
      <div className="flex flex-col items-center py-4 gap-1">
        <div className="mb-4 text-center">
          <motion.div
            animate={{ boxShadow: connected ? '0 0 20px #00f0ff' : 'none' }}
            className={cn(
              'w-8 h-8 rounded-full border-2 flex items-center justify-center',
              connected ? 'border-aether-cyan' : 'border-aether-cyan/30',
            )}
          >
            <span className="text-[8px] font-hud text-aether-cyan">Æ</span>
          </motion.div>
        </div>

        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveScreen(id)}
            title={label}
            className={cn(
              'group relative w-11 h-11 flex items-center justify-center transition-all duration-200',
              activeScreen === id
                ? 'text-aether-cyan'
                : 'text-aether-cyan/30 hover:text-aether-cyan/70',
            )}
          >
            {activeScreen === id && (
              <motion.div
                layoutId="nav-indicator"
                className="absolute inset-0 border border-aether-cyan/50 bg-aether-cyan/5"
                style={{ boxShadow: '0 0 15px rgba(0,240,255,0.2)' }}
              />
            )}
            <Icon size={18} />
            <span className="absolute left-full ml-2 px-2 py-1 text-[10px] font-mono uppercase tracking-widest bg-black/90 border border-aether-border opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
              {label}
            </span>
          </button>
        ))}
      </div>
    </motion.nav>
  );
}
