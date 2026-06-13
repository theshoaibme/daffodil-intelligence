import type { UiBlock, UiBlockSchema } from "./types";

const KNOWN_SCHEMAS = new Set<string>([
  "data_table",
  "key_value",
  "tabs",
  "status_card",
  "error_alert",
]);

function inferSchema(data: Record<string, unknown>): UiBlockSchema | string {
  if (Array.isArray(data.rows)) return "data_table";
  if (Array.isArray(data.items)) return "data_table";
  if (data.weekly && typeof data.weekly === "object") return "data_table";
  if (data.classes || data.reminders || data.routines) return "data_table";
  if (data.message != null) return "status_card";
  return "key_value";
}

/** Normalize wire JSON (schema / block_type aliases) into a UiBlock. */
export function coerceUiBlock(raw: unknown): UiBlock | null {
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;
  const data = (record.data as Record<string, unknown>) ?? {};
  let schema = String(record.schema || record.block_type || "").trim();
  if (!schema || !KNOWN_SCHEMAS.has(schema)) {
    schema = inferSchema(data);
  }
  const id = String(record.id || `ui-${Math.random().toString(36).slice(2, 10)}`);
  return {
    id,
    schema: schema as UiBlockSchema,
    title: (record.title as string | null | undefined) ?? null,
    data,
    source: (record.source as string | null | undefined) ?? null,
  };
}

export function coerceUiBlocks(raw: unknown): UiBlock[] {
  if (!Array.isArray(raw)) return [];
  return raw.map(coerceUiBlock).filter((b): b is UiBlock => b != null);
}

/** Merge block lists; later entries with the same id win. */
export function mergeUiBlocks(...lists: Array<UiBlock[] | unknown[]>): UiBlock[] {
  const byId = new Map<string, UiBlock>();
  for (const list of lists) {
    for (const item of list) {
      const block = coerceUiBlock(item);
      if (block) byId.set(block.id, block);
    }
  }
  return Array.from(byId.values());
}
