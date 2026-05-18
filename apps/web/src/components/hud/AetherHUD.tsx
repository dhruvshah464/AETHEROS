'use client';

import dynamic from 'next/dynamic';
import { AnimatePresence, motion } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';
import { CommandCenter } from '@/components/screens/CommandCenter';
import { TelemetryScreen } from '@/components/screens/TelemetryScreen';
import { AgentNetwork } from '@/components/screens/AgentNetwork';
import { VisionScreen } from '@/components/screens/VisionScreen';
import { MemoryScreen } from '@/components/screens/MemoryScreen';
import { VoiceScreen } from '@/components/screens/VoiceScreen';
import { BrowserControl } from '@/components/screens/BrowserControl';
import { MissionDashboard } from '@/components/screens/MissionDashboard';
import { NeuralActivity } from '@/components/screens/NeuralActivity';
import { ModelsDashboard } from '@/components/screens/ModelsDashboard';
import { DiagnosticsScreen } from '@/components/screens/DiagnosticsScreen';
import { SecurityConsole } from '@/components/screens/SecurityConsole';
import { AgentStudio } from '@/components/screens/AgentStudio';
import { PluginMarketplace } from '@/components/screens/PluginMarketplace';
import { FUIShader } from '@/components/hud/FUIShader';
import { useAetherStore } from '@/store/aether-store';
import { useWebSocket } from '@/hooks/use-websocket';

const HolographicBackground = dynamic(
  () => import('./HolographicBackground').then((m) => m.HolographicBackground),
  { ssr: false },
);

const SCREEN_VARIANTS = {
  initial: { opacity: 0, scale: 0.98 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.98 },
};

export function AetherHUD() {
  const activeScreen = useAetherStore((s) => s.activeScreen);
  const { sendCommand } = useWebSocket();

  const renderScreen = () => {
    switch (activeScreen) {
      case 'command':
        return <CommandCenter onSend={sendCommand} />;
      case 'telemetry':
        return <TelemetryScreen />;
      case 'agents':
        return <AgentNetwork />;
      case 'vision':
        return <VisionScreen />;
      case 'memory':
        return <MemoryScreen />;
      case 'voice':
        return <VoiceScreen />;
      case 'browser':
        return <BrowserControl />;
      case 'mission':
        return <MissionDashboard />;
      case 'neural':
        return <NeuralActivity />;
      case 'models':
        return <ModelsDashboard />;
      case 'diagnostics':
        return <DiagnosticsScreen />;
      case 'security':
        return <SecurityConsole />;
      case 'studio':
        return <AgentStudio />;
      case 'marketplace':
        return <PluginMarketplace />;
      default:
        return <CommandCenter onSend={sendCommand} />;
    }
  };

  return (
    <div className="scanlines grid-bg relative flex flex-col h-screen w-screen overflow-hidden bg-[#030508]">
      <HolographicBackground />
      <FUIShader />
      <StatusBar />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 p-4 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeScreen}
              variants={SCREEN_VARIANTS}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.25 }}
              className="h-full"
            >
              {renderScreen()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
