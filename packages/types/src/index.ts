/** Core domain types for AetherOS realtime event system */

export type AgentId =
  | 'commander'
  | 'research'
  | 'coding'
  | 'vision'
  | 'planning'
  | 'security'
  | 'automation'
  | 'voice';

export type AgentStatus = 'idle' | 'thinking' | 'executing' | 'waiting' | 'error' | 'complete';

export type EventChannel =
  | 'system'
  | 'telemetry'
  | 'ai'
  | 'agent'
  | 'vision'
  | 'voice'
  | 'memory'
  | 'automation'
  | 'browser';

export type EventType =
  // System
  | 'system.connected'
  | 'system.heartbeat'
  | 'system.error'
  // Telemetry
  | 'telemetry.snapshot'
  | 'telemetry.gpu'
  | 'telemetry.process'
  // AI
  | 'ai.stream.start'
  | 'ai.stream.token'
  | 'ai.stream.thought'
  | 'ai.stream.end'
  | 'ai.command.queued'
  | 'ai.command.complete'
  // Agent
  | 'agent.status'
  | 'agent.message'
  | 'agent.handoff'
  | 'agent.task.start'
  | 'agent.task.progress'
  | 'agent.task.complete'
  // Vision
  | 'vision.frame'
  | 'vision.detection'
  | 'vision.scene'
  // Voice
  | 'voice.wake'
  | 'voice.transcript'
  | 'voice.response'
  | 'voice.speaking'
  // Memory
  | 'memory.store'
  | 'memory.recall'
  | 'memory.search'
  // Automation
  | 'automation.action'
  | 'automation.approval.request'
  | 'automation.approval.granted'
  | 'browser.navigation'
  | 'browser.screenshot'
  | 'browser.action'
  | 'browser.cursor'
  | 'terminal.output'
  | 'terminal.command'
  | 'workflow.start'
  | 'workflow.node.start'
  | 'workflow.node.complete'
  | 'workflow.complete'
  | 'screen.capture'
  | 'demo.start'
  | 'demo.step'
  | 'demo.complete'
  | 'model.status';

export interface AetherEvent<T = unknown> {
  id: string;
  type: EventType;
  channel: EventChannel;
  timestamp: number;
  sessionId: string;
  payload: T;
  metadata?: Record<string, unknown>;
}

export interface TelemetrySnapshot {
  cpu: {
    percent: number;
    cores: number;
    freqMhz: number;
  };
  memory: {
    totalGb: number;
    usedGb: number;
    percent: number;
  };
  disk: {
    totalGb: number;
    usedGb: number;
    percent: number;
  };
  network: {
    bytesSent: number;
    bytesRecv: number;
    packetsSent: number;
    packetsRecv: number;
  };
  gpu?: {
    name: string;
    utilization: number;
    memoryUsedMb: number;
    memoryTotalMb: number;
    temperature?: number;
  }[];
  processes: ProcessInfo[];
  aiUsage: {
    tokensIn: number;
    tokensOut: number;
    activeModels: string[];
    inferenceLatencyMs: number;
  };
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpuPercent: number;
  memoryMb: number;
}

export interface AgentNode {
  id: AgentId;
  name: string;
  status: AgentStatus;
  currentTask?: string;
  progress?: number;
  lastActivity: number;
}

export interface AgentMessage {
  from: AgentId;
  to: AgentId | 'broadcast';
  content: string;
  type: 'request' | 'response' | 'handoff' | 'status';
}

export interface AIStreamToken {
  token: string;
  index: number;
  model: string;
  finishReason?: string;
}

export interface AIThought {
  step: number;
  content: string;
  type: 'reasoning' | 'planning' | 'action' | 'observation';
}

export interface VisionDetection {
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
  trackId?: number;
}

export interface MemoryEntry {
  id: string;
  content: string;
  type: 'episodic' | 'semantic' | 'procedural';
  timestamp: number;
  embedding?: number[];
  metadata?: Record<string, unknown>;
}

export interface CommandRequest {
  id: string;
  prompt: string;
  context?: string;
  agentId?: AgentId;
  tools?: string[];
  stream?: boolean;
}

export interface CommandResponse {
  id: string;
  content: string;
  thoughts: AIThought[];
  agentId: AgentId;
  tokensUsed: number;
  latencyMs: number;
}

export interface AutomationAction {
  id: string;
  type: 'browser' | 'terminal' | 'file' | 'ui';
  description: string;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'awaiting_approval';
  result?: string;
}

export interface BrowserActionLog {
  id: string;
  type: string;
  description: string;
  status: string;
  result?: string;
  params?: Record<string, unknown>;
  timestamp?: number;
}

export interface BrowserState {
  active: boolean;
  url: string;
  mode: string;
  streaming: boolean;
  pendingApprovals: number;
  actionLog: BrowserActionLog[];
}

export interface WorkflowNodeState {
  id: string;
  type: string;
  label: string;
  status: string;
  dependsOn: string[];
  result?: unknown;
  error?: string;
}

export interface WorkflowState {
  id: string;
  name: string;
  status: string;
  createdAt: number;
  nodes: WorkflowNodeState[];
}

export interface TerminalLogEntry {
  id: string;
  command: string;
  cwd: string;
  status: string;
  output: string;
  exitCode?: number;
  timestamp: number;
}

export interface ModelInfo {
  id: string;
  provider: string;
  size?: number;
  modified?: string;
}

export type ScreenId =
  | 'command'
  | 'vision'
  | 'agents'
  | 'telemetry'
  | 'memory'
  | 'browser'
  | 'voice'
  | 'mission'
  | 'neural'
  | 'models'
  | 'diagnostics'
  | 'security'
  | 'studio'
  | 'marketplace';

export interface WSMessage {
  action: 'subscribe' | 'unsubscribe' | 'publish' | 'ping' | 'command';
  channels?: EventChannel[];
  event?: AetherEvent;
  command?: CommandRequest;
}
