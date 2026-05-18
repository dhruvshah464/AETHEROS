import { create } from 'zustand';
import type {
  AgentNode,
  AetherEvent,
  AIThought,
  BrowserActionLog,
  MemoryEntry,
  ScreenId,
  TelemetrySnapshot,
  TerminalLogEntry,
  VisionDetection,
  WorkflowState,
} from '@aetheros/types';

interface AetherState {
  connected: boolean;
  sessionId: string | null;
  activeScreen: ScreenId;
  setActiveScreen: (screen: ScreenId) => void;

  telemetry: TelemetrySnapshot | null;
  setTelemetry: (data: TelemetrySnapshot) => void;

  aiStreaming: boolean;
  aiResponse: string;
  aiThoughts: AIThought[];
  appendAiToken: (token: string) => void;
  addThought: (thought: AIThought) => void;
  clearAi: () => void;
  setAiStreaming: (streaming: boolean) => void;

  agents: AgentNode[];
  agentMessages: Array<{ from: string; to: string; content: string; timestamp: number }>;
  setAgents: (agents: AgentNode[]) => void;
  addAgentMessage: (msg: { from: string; to: string; content: string }) => void;

  detections: VisionDetection[];
  setDetections: (detections: VisionDetection[]) => void;
  sceneAnalysis: string;
  setSceneAnalysis: (text: string) => void;
  screenCapture: string | null;
  setScreenCapture: (b64: string | null) => void;

  memories: MemoryEntry[];
  addMemory: (entry: MemoryEntry) => void;

  eventLog: AetherEvent[];
  pushEvent: (event: AetherEvent) => void;

  voiceActive: boolean;
  transcript: string;
  voiceResponse: string;
  voiceAudio: string | null;
  voiceSpeaking: boolean;
  setVoiceActive: (active: boolean) => void;
  setTranscript: (text: string) => void;
  setVoiceResponse: (text: string) => void;
  setVoiceAudio: (b64: string | null) => void;
  setVoiceSpeaking: (speaking: boolean) => void;

  browserScreenshot: string | null;
  browserUrl: string;
  browserActions: BrowserActionLog[];
  browserMode: string;
  browserStreaming: boolean;
  pendingApproval: BrowserActionLog | null;
  setBrowserScreenshot: (b64: string | null) => void;
  setBrowserUrl: (url: string) => void;
  addBrowserAction: (action: BrowserActionLog) => void;
  setBrowserMode: (mode: string) => void;
  setBrowserStreaming: (streaming: boolean) => void;
  setPendingApproval: (action: BrowserActionLog | null) => void;

  terminalOutput: string;
  terminalLogs: TerminalLogEntry[];
  appendTerminalOutput: (line: string) => void;
  addTerminalLog: (entry: TerminalLogEntry) => void;
  clearTerminalOutput: () => void;

  workflows: WorkflowState[];
  activeWorkflow: WorkflowState | null;
  setWorkflows: (wfs: WorkflowState[]) => void;
  setActiveWorkflow: (wf: WorkflowState | null) => void;
  updateWorkflow: (wf: WorkflowState) => void;

  demoRunning: boolean;
  demoStep: string;
  setDemoRunning: (running: boolean) => void;
  setDemoStep: (step: string) => void;

  models: Array<{ id: string; provider: string }>;
  providers: Array<{ name: string; status: string }>;
  neuralTokens: number[];
  setModels: (data: { models: Array<{ id: string; provider: string }>; providers: Array<{ name: string; status: string }> }) => void;
  pushNeuralToken: () => void;
}

export const useAetherStore = create<AetherState>((set) => ({
  connected: false,
  sessionId: null,
  activeScreen: 'command',
  setActiveScreen: (screen) => set({ activeScreen: screen }),

  telemetry: null,
  setTelemetry: (data) => set({ telemetry: data as TelemetrySnapshot }),

  aiStreaming: false,
  aiResponse: '',
  aiThoughts: [],
  appendAiToken: (token) => set((s) => ({ aiResponse: s.aiResponse + token })),
  addThought: (thought) => set((s) => ({ aiThoughts: [...s.aiThoughts, thought] })),
  clearAi: () => set({ aiResponse: '', aiThoughts: [] }),
  setAiStreaming: (streaming) => set({ aiStreaming: streaming }),

  agents: [],
  agentMessages: [],
  setAgents: (agents) => set({ agents }),
  addAgentMessage: (msg) =>
    set((s) => ({
      agentMessages: [...s.agentMessages.slice(-50), { ...msg, timestamp: Date.now() }],
    })),

  detections: [],
  setDetections: (detections) => set({ detections }),
  sceneAnalysis: '',
  setSceneAnalysis: (text) => set({ sceneAnalysis: text }),
  screenCapture: null,
  setScreenCapture: (b64) => set({ screenCapture: b64 }),

  memories: [],
  addMemory: (entry) => set((s) => ({ memories: [entry, ...s.memories].slice(0, 100) })),

  eventLog: [],
  pushEvent: (event) => set((s) => ({ eventLog: [event, ...s.eventLog].slice(0, 300) })),

  voiceActive: false,
  transcript: '',
  voiceResponse: '',
  voiceAudio: null,
  voiceSpeaking: false,
  setVoiceActive: (active) => set({ voiceActive: active }),
  setTranscript: (text) => set({ transcript: text }),
  setVoiceResponse: (text) => set({ voiceResponse: text }),
  setVoiceAudio: (b64) => set({ voiceAudio: b64 }),
  setVoiceSpeaking: (speaking) => set({ voiceSpeaking: speaking }),

  browserScreenshot: null,
  browserUrl: '',
  browserActions: [],
  browserMode: 'safe',
  browserStreaming: false,
  pendingApproval: null,
  setBrowserScreenshot: (b64) => set({ browserScreenshot: b64 }),
  setBrowserUrl: (url) => set({ browserUrl: url }),
  addBrowserAction: (action) =>
    set((s) => ({
      browserActions: [action, ...s.browserActions.filter((a) => a.id !== action.id)].slice(0, 100),
    })),
  setBrowserMode: (mode) => set({ browserMode: mode }),
  setBrowserStreaming: (streaming) => set({ browserStreaming: streaming }),
  setPendingApproval: (action) => set({ pendingApproval: action }),

  terminalOutput: '',
  terminalLogs: [],
  appendTerminalOutput: (line) => set((s) => ({ terminalOutput: s.terminalOutput + line })),
  addTerminalLog: (entry) => set((s) => ({ terminalLogs: [entry, ...s.terminalLogs].slice(0, 50) })),
  clearTerminalOutput: () => set({ terminalOutput: '' }),

  workflows: [],
  activeWorkflow: null,
  setWorkflows: (wfs) => set({ workflows: wfs }),
  setActiveWorkflow: (wf) => set({ activeWorkflow: wf }),
  updateWorkflow: (wf) =>
    set((s) => ({
      workflows: s.workflows.map((w) => (w.id === wf.id ? wf : w)),
      activeWorkflow: s.activeWorkflow?.id === wf.id ? wf : s.activeWorkflow,
    })),

  demoRunning: false,
  demoStep: '',
  setDemoRunning: (running) => set({ demoRunning: running }),
  setDemoStep: (step) => set({ demoStep: step }),

  models: [],
  providers: [],
  neuralTokens: Array(24).fill(0),
  setModels: (data) => set({ models: data.models, providers: data.providers }),
  pushNeuralToken: () =>
    set((s) => ({
      neuralTokens: [...s.neuralTokens.slice(1), Math.floor(Math.random() * 100)],
    })),
}));
