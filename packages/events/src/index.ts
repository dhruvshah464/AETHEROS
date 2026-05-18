import type { AetherEvent, EventChannel, EventType } from '@aetheros/types';

export function createEventId(): string {
  return `evt_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export function createEvent<T>(
  type: EventType,
  channel: EventChannel,
  payload: T,
  sessionId = 'global',
  metadata?: Record<string, unknown>,
): AetherEvent<T> {
  return {
    id: createEventId(),
    type,
    channel,
    timestamp: Date.now(),
    sessionId,
    payload,
    metadata,
  };
}

export type EventHandler<T = unknown> = (event: AetherEvent<T>) => void;

export class EventBus {
  private handlers = new Map<string, Set<EventHandler>>();
  private channelHandlers = new Map<EventChannel, Set<EventHandler>>();

  subscribe(channel: EventChannel, handler: EventHandler): () => void {
    if (!this.channelHandlers.has(channel)) {
      this.channelHandlers.set(channel, new Set());
    }
    this.channelHandlers.get(channel)!.add(handler);
    return () => this.channelHandlers.get(channel)?.delete(handler);
  }

  subscribeType(type: EventType, handler: EventHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  publish<T>(event: AetherEvent<T>): void {
    this.handlers.get(event.type)?.forEach((h) => h(event as AetherEvent));
    this.channelHandlers.get(event.channel)?.forEach((h) => h(event as AetherEvent));
  }

  clear(): void {
    this.handlers.clear();
    this.channelHandlers.clear();
  }
}

export { type AetherEvent, type EventChannel, type EventType } from '@aetheros/types';
