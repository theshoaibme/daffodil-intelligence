import type { AiEventEnvelope } from "./types";

type Handler = (event: AiEventEnvelope) => void;

class EventBus {
  private handlers = new Map<string, Set<Handler>>();
  private buffer: AiEventEnvelope[] = [];
  private rafId: number | null = null;
  private flushCallback: ((events: AiEventEnvelope[]) => void) | null = null;

  setFlushCallback(fn: (events: AiEventEnvelope[]) => void) {
    this.flushCallback = fn;
  }

  subscribe(type: string | "*", fn: Handler): () => void {
    const key = type;
    if (!this.handlers.has(key)) {
      this.handlers.set(key, new Set());
    }
    this.handlers.get(key)!.add(fn);
    return () => {
      this.handlers.get(key)?.delete(fn);
    };
  }

  publish(event: AiEventEnvelope) {
    this.buffer.push(event);
    if (this.rafId != null) return;
    this.rafId = requestAnimationFrame(() => {
      const batch = this.buffer.splice(0);
      this.rafId = null;
      this.dispatch(batch);
      this.flushCallback?.(batch);
    });
  }

  publishImmediate(event: AiEventEnvelope) {
    this.dispatch([event]);
    this.flushCallback?.([event]);
  }

  private dispatch(batch: AiEventEnvelope[]) {
    for (const event of batch) {
      this.handlers.get(event.type)?.forEach((h) => h(event));
      this.handlers.get("*")?.forEach((h) => h(event));
    }
  }

  flush() {
    if (this.rafId != null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    if (this.buffer.length) {
      const batch = this.buffer.splice(0);
      this.dispatch(batch);
      this.flushCallback?.(batch);
    }
  }

  clearPending() {
    if (this.rafId != null) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    this.buffer = [];
  }
}

export const eventBus = new EventBus();
