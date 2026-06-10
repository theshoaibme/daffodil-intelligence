import type { UiBlock, UiTableColumn } from "./types";

function columnsFromRows(rows: Record<string, unknown>[]): UiTableColumn[] {
  const keys: string[] = [];
  for (const row of rows) {
    for (const k of Object.keys(row)) {
      if (!keys.includes(k)) keys.push(k);
    }
  }
  return keys.map((key) => ({ key, label: key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) }));
}

function flattenWeekly(weekly: Record<string, unknown>): Record<string, unknown>[] {
  const rows: Record<string, unknown>[] = [];
  for (const [day, items] of Object.entries(weekly)) {
    if (!Array.isArray(items)) continue;
    for (const item of items) {
      if (item && typeof item === "object") {
        rows.push({ day, ...(item as Record<string, unknown>) });
      }
    }
  }
  return rows;
}

function asDataTable(
  block: UiBlock,
  rows: Record<string, unknown>[],
  title?: string | null
): UiBlock {
  return {
    ...block,
    schema: "data_table",
    title: title ?? block.title,
    data: { columns: columnsFromRows(rows), rows },
  };
}

/** Convert legacy or raw tool payloads into generic data_table blocks. */
export function normalizeUiBlocks(blocks: UiBlock[]): UiBlock[] {
  return blocks.flatMap((block) => normalizeOneBlock(block));
}

function normalizeOneBlock(block: UiBlock): UiBlock[] {
  const schema =
    block.schema ||
    (block as UiBlock & { block_type?: string }).block_type ||
    "data_table";
  const data = block.data ?? {};

  if (schema === "data_table" && Array.isArray(data.rows)) {
    const rows = data.rows as Record<string, unknown>[];
    const columns = (data.columns as UiTableColumn[])?.length
      ? (data.columns as UiTableColumn[])
      : columnsFromRows(rows);
    return [{ ...block, schema: "data_table", data: { columns, rows } }];
  }

  if (schema === "status_card" || schema === "error_alert" || schema === "tabs" || schema === "key_value") {
    return [block];
  }

  // Legacy: routine_weekly / raw weekly object
  if (data.weekly && typeof data.weekly === "object") {
    const rows = flattenWeekly(data.weekly as Record<string, unknown>);
    const sec = data.section as string | undefined;
    const title = block.title ?? (sec ? `Class routine — ${sec}` : "Class routine");
    return rows.length
      ? [asDataTable(block, rows, title)]
      : [{ ...block, schema: "status_card", data: { tone: "info", message: "No routine data yet." }, title }];
  }

  // Legacy: routine_day / items list
  if (Array.isArray(data.items)) {
    const rows = data.items as Record<string, unknown>[];
    return rows.length
      ? [asDataTable(block, rows, block.title)]
      : [{ ...block, schema: "status_card", data: { tone: "info", message: "No classes on this day." }, title: block.title }];
  }

  // Legacy: daily_schedule or combined day view
  if (data.classes || (schema === "daily_schedule" && data.day)) {
    const day = (data.day as string) ?? "Today";
    const sec = (data.section as string) ?? "";
    const base = sec ? `${day} · ${sec}` : day;
    const out: UiBlock[] = [];
    for (const [key, label] of [
      ["classes", "Classes"],
      ["reminders", "Reminders"],
      ["routines", "Routines"],
    ] as const) {
      const list = data[key];
      if (Array.isArray(list) && list.length) {
        out.push(
          asDataTable(
            { ...block, id: `${block.id}-${key}` },
            list as Record<string, unknown>[],
            `${base} — ${label}`
          )
        );
      }
    }
    return out.length ? out : [{ ...block, schema: "status_card", data: { tone: "info", message: "Nothing scheduled." }, title: base }];
  }

  // Legacy list wrappers
  for (const key of ["reminders", "routines", "hooks"] as const) {
    const list = data[key];
    if (Array.isArray(list) && list.length && typeof list[0] === "object") {
      return [asDataTable(block, list as Record<string, unknown>[], block.title ?? key.replace("_", " "))];
    }
  }

  // Single list at root
  if (Array.isArray(data.rows) && typeof data.rows[0] === "object") {
    const rows = data.rows as Record<string, unknown>[];
    return [asDataTable(block, rows, block.title)];
  }

  return [block];
}
