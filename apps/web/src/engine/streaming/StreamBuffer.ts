export class StreamBuffer {
  private chunks: string[] = [];
  private committed = "";
  private raf: number | null = null;
  private onUpdate: (full: string, delta: string) => void;

  constructor(onUpdate: (full: string, delta: string) => void) {
    this.onUpdate = onUpdate;
  }

  push(chunk: string) {
    if (!chunk) return;
    this.chunks.push(chunk);
    this.scheduleFlush();
  }

  private scheduleFlush() {
    if (this.raf != null) return;
    this.raf = requestAnimationFrame(() => {
      const delta = this.chunks.splice(0).join("");
      this.committed += delta;
      this.raf = null;
      this.onUpdate(this.committed, delta);
    });
  }

  finalize(): string {
    if (this.raf != null) {
      cancelAnimationFrame(this.raf);
      this.raf = null;
    }
    const delta = this.chunks.splice(0).join("");
    this.committed += delta;
    if (delta) this.onUpdate(this.committed, delta);
    return this.committed;
  }

  reset() {
    if (this.raf != null) cancelAnimationFrame(this.raf);
    this.raf = null;
    this.chunks = [];
    this.committed = "";
  }

  get value() {
    return this.committed;
  }
}
