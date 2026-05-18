'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { HUDPanel } from '@/components/hud/HUDPanel';
import { useAetherStore } from '@/store/aether-store';
import { API_URL } from '@/lib/utils';

const STATUS_COLORS: Record<string, string> = {
  idle: '#00f0ff44',
  thinking: '#ffd700',
  executing: '#00ff88',
  waiting: '#7b61ff',
  error: '#ff3366',
  complete: '#00f0ff',
};

export function AgentNetwork() {
  const { agents, agentMessages } = useAetherStore();

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await fetch(`${API_URL}/ai/agents`);
        const data = await res.json();
        if (data.agents) useAetherStore.getState().setAgents(data.agents);
      } catch {
        // Use default agents when API offline
        useAetherStore.getState().setAgents(
          ['commander', 'research', 'coding', 'vision', 'planning', 'security', 'automation', 'voice'].map(
            (id) => ({
              id: id as never,
              name: id.toUpperCase(),
              status: 'idle' as const,
              lastActivity: Date.now(),
            }),
          ),
        );
      }
    };
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
      <HUDPanel title="Agent Network Topology" className="lg:col-span-2" delay={0.1}>
        <div className="p-6 relative min-h-[400px]">
          {/* Central commander */}
          <motion.div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10"
            animate={{ boxShadow: ['0 0 20px #00f0ff44', '0 0 40px #00f0ff88', '0 0 20px #00f0ff44'] }}
            transition={{ repeat: Infinity, duration: 3 }}
          >
            <AgentNodeVisual
              name="COMMANDER"
              status={agents.find((a) => a.id === 'commander')?.status ?? 'idle'}
              size="lg"
            />
          </motion.div>

          {/* Orbiting agents */}
          {agents
            .filter((a) => a.id !== 'commander')
            .map((agent, i) => {
              const angle = (i / (agents.length - 1)) * Math.PI * 2 - Math.PI / 2;
              const radius = 140;
              const x = Math.cos(angle) * radius;
              const y = Math.sin(angle) * radius;
              return (
                <motion.div
                  key={agent.id}
                  className="absolute top-1/2 left-1/2"
                  style={{ transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))` }}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <svg
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
                    style={{ width: Math.abs(x) * 2 + 60, height: Math.abs(y) * 2 + 60, transform: `translate(calc(-50% - ${x/2}px), calc(-50% - ${y/2}px))` }}
                  >
                    <line
                      x1="50%"
                      y1="50%"
                      x2={x > 0 ? '0%' : '100%'}
                      y2={y > 0 ? '0%' : '100%'}
                      stroke="rgba(0,240,255,0.15)"
                      strokeWidth="1"
                    />
                  </svg>
                  <AgentNodeVisual
                    name={agent.name || agent.id}
                    status={agent.status}
                    task={agent.currentTask}
                    progress={agent.progress}
                  />
                </motion.div>
              );
            })}
        </div>
      </HUDPanel>

      <HUDPanel title="Inter-Agent Comms" delay={0.2}>
        <div className="p-4 space-y-2 overflow-y-auto max-h-[500px]">
          {agentMessages.length === 0 ? (
            <p className="hud-label">No active inter-agent communication</p>
          ) : (
            agentMessages
              .slice()
              .reverse()
              .map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-2 border border-aether-border/20 font-mono text-[10px]"
                >
                  <span className="text-aether-cyan">{msg.from}</span>
                  <span className="text-aether-cyan/30"> → </span>
                  <span className="text-aether-purple">{msg.to}</span>
                  <p className="text-aether-cyan/60 mt-1">{msg.content}</p>
                </motion.div>
              ))
          )}
        </div>
      </HUDPanel>
    </div>
  );
}

function AgentNodeVisual({
  name,
  status,
  task,
  progress,
  size = 'sm',
}: {
  name: string;
  status: string;
  task?: string;
  progress?: number;
  size?: 'sm' | 'lg';
}) {
  const color = STATUS_COLORS[status] ?? STATUS_COLORS.idle;
  const dim = size === 'lg' ? 'w-20 h-20' : 'w-14 h-14';

  return (
    <div className="flex flex-col items-center gap-1">
      <motion.div
        animate={status === 'executing' ? { scale: [1, 1.05, 1] } : {}}
        transition={{ repeat: Infinity, duration: 1 }}
        className={`${dim} rounded-full border-2 flex items-center justify-center`}
        style={{ borderColor: color, boxShadow: `0 0 15px ${color}44` }}
      >
        <span className="font-mono text-[8px] text-aether-cyan text-center leading-tight px-1">
          {name.slice(0, 6)}
        </span>
      </motion.div>
      <span className="hud-label text-[8px]" style={{ color }}>
        {status}
      </span>
      {task && (
        <span className="font-mono text-[8px] text-aether-cyan/40 max-w-[80px] truncate">
          {task}
        </span>
      )}
      {progress !== undefined && progress > 0 && (
        <div className="w-12 h-0.5 bg-aether-cyan/10 rounded">
          <div className="h-full bg-aether-cyan rounded" style={{ width: `${progress * 100}%` }} />
        </div>
      )}
    </div>
  );
}
