'use client';

import { useEffect, useRef, useCallback } from 'react';
import type {
  AetherEvent,
  AgentNode,
  BrowserActionLog,
  TelemetrySnapshot,
  VisionDetection,
  WorkflowState,
} from '@aetheros/types';
import { useAetherStore } from '@/store/aether-store';
import { WS_URL } from '@/lib/utils';

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const {
    setTelemetry,
    appendAiToken,
    setAiStreaming,
    clearAi,
    setAgents,
    addAgentMessage,
    setDetections,
    addMemory,
    pushEvent,
  } = useAetherStore();

  const handleEvent = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;
      const channel = (data.channel as string) || 'system';
      const payload = (data.payload as Record<string, unknown>) || {};

      const event: AetherEvent = {
        id: (data.id as string) || `evt_${Date.now()}`,
        type: type as AetherEvent['type'],
        channel: channel as AetherEvent['channel'],
        timestamp: (data.timestamp as number) || Date.now(),
        sessionId: (data.sessionId as string) || 'global',
        payload,
      };

      pushEvent(event);

      switch (type) {
        case 'system.connected':
          useAetherStore.setState({ connected: true, sessionId: payload.sessionId as string });
          break;

        case 'telemetry.snapshot':
          setTelemetry(payload as unknown as TelemetrySnapshot);
          break;

        case 'ai.stream.start':
          clearAi();
          setAiStreaming(true);
          break;

        case 'ai.stream.token':
          appendAiToken((payload.token as string) || '');
          useAetherStore.getState().pushNeuralToken();
          break;

        case 'ai.stream.end':
          setAiStreaming(false);
          break;

        case 'agent.status':
          fetchAgents();
          break;

        case 'agent.message':
          addAgentMessage({
            from: payload.from as string,
            to: payload.to as string,
            content: payload.content as string,
          });
          break;

        case 'vision.detection':
          setDetections((payload.detections as VisionDetection[]) || []);
          break;

        case 'memory.store':
          addMemory(payload as unknown as Parameters<typeof addMemory>[0]);
          break;

        case 'browser.screenshot':
          useAetherStore.getState().setBrowserScreenshot((payload.screenshot as string) || null);
          if (payload.url) useAetherStore.getState().setBrowserUrl(payload.url as string);
          break;

        case 'browser.action':
          useAetherStore.getState().addBrowserAction(payload as unknown as BrowserActionLog);
          if (payload.status === 'awaiting_approval') {
            useAetherStore.getState().setPendingApproval(payload as unknown as BrowserActionLog);
          }
          break;

        case 'browser.navigation':
          useAetherStore.getState().setBrowserUrl((payload.url as string) || '');
          break;

        case 'automation.approval.request':
          useAetherStore.getState().setPendingApproval({
            id: payload.actionId as string,
            type: 'approval',
            description: payload.description as string,
            status: 'awaiting_approval',
          });
          break;

        case 'terminal.output':
          useAetherStore.getState().appendTerminalOutput(payload.line as string);
          break;

        case 'workflow.start':
        case 'workflow.node.start':
        case 'workflow.node.complete':
        case 'workflow.complete':
          fetchWorkflows();
          break;

        case 'voice.transcript':
          useAetherStore.getState().setTranscript((payload.text as string) || '');
          break;

        case 'voice.response':
          useAetherStore.getState().setVoiceResponse((payload.text as string) || '');
          break;

        case 'voice.audio':
          useAetherStore.getState().setVoiceAudio((payload.audio as string) || null);
          break;

        case 'voice.speaking':
          useAetherStore.getState().setVoiceSpeaking(payload.status === 'start');
          break;

        case 'vision.scene':
          useAetherStore.getState().setSceneAnalysis((payload.analysis as string) || '');
          break;

        case 'screen.capture':
          useAetherStore.getState().setScreenCapture((payload.screenshot as string) || null);
          break;

        case 'demo.start':
          useAetherStore.getState().setDemoRunning(true);
          break;

        case 'demo.step':
          useAetherStore.getState().setDemoStep((payload.message as string) || '');
          break;

        case 'demo.complete':
          useAetherStore.getState().setDemoRunning(false);
          useAetherStore.getState().setDemoStep('');
          break;
      }
    },
    [
      setTelemetry,
      appendAiToken,
      setAiStreaming,
      clearAi,
      addAgentMessage,
      setDetections,
      addMemory,
      pushEvent,
    ],
  );

  const fetchWorkflows = async () => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/workflow/list/all`,
      );
      const data = await res.json();
      if (data.workflows) useAetherStore.getState().setWorkflows(data.workflows as WorkflowState[]);
    } catch {
      /* offline */
    }
  };

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/ai/agents`);
      const data = await res.json();
      if (data.agents) {
        setAgents(data.agents as AgentNode[]);
      }
    } catch {
      // API offline
    }
  };

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      useAetherStore.setState({ connected: true });
      fetchAgents();

      // Heartbeat
      const interval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: 'ping', timestamp: Date.now() }));
        }
      }, 30000);

      ws.addEventListener('close', () => clearInterval(interval));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'history' && Array.isArray(data.events)) {
          data.events.forEach((e: Record<string, unknown>) => handleEvent(e));
          return;
        }

        handleEvent(data);
      } catch {
        // Binary or invalid
      }
    };

    ws.onclose = () => {
      useAetherStore.setState({ connected: false });
      reconnectRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, [handleEvent]);

  const sendCommand = useCallback((prompt: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      clearAi();
      setAiStreaming(true);
      wsRef.current.send(
        JSON.stringify({
          action: 'command',
          command: { prompt, stream: true },
        }),
      );
    } else {
      // Fallback to HTTP SSE
      streamViaHttp(prompt);
    }
  }, [clearAi, setAiStreaming]);

  const streamViaHttp = async (prompt: string) => {
    clearAi();
    setAiStreaming(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/ai/command`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt, stream: true, use_agents: true }),
        },
      );

      const reader = res.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split('\n')) {
          if (line.startsWith('data: ')) {
            const token = line.slice(6);
            if (token === '[DONE]') break;
            appendAiToken(token);
          }
        }
      }
    } catch {
      appendAiToken('[Connection failed — start API server on port 8000]');
    } finally {
      setAiStreaming(false);
    }
  };

  useEffect(() => {
    connect();
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { sendCommand, reconnect: connect };
}
