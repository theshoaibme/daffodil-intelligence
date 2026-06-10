import type { UiBlock } from "./types";

const TOOL_CALL_LINE = /^\s*[a-z][a-z0-9_]*\s*\([^)]*\)\s*$/i;
const TOOL_CALL_INLINE = /\b[a-z][a-z0-9_]*\s*\([^)]*\)/gi;

function hasRoutineTable(blocks: UiBlock[]): boolean {
  return blocks.some((block) => {
    if (block.schema !== "data_table") return false;
    const rows = block.data?.rows;
    return Array.isArray(rows) && rows.length > 0;
  });
}

/** Remove tool-call syntax and duplicate prose when structured UI blocks are present. */
export function sanitizeAssistantContent(content: string, blocks: UiBlock[] = []): string {
  let text = (content || "").trim();
  if (!text) return text;

  text = text
    .split("\n")
    .filter((line) => !TOOL_CALL_LINE.test(line.trim()))
    .join("\n")
    .replace(TOOL_CALL_INLINE, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  if (!hasRoutineTable(blocks)) {
    return text;
  }

  // Drop invented schedule bullets when a data table already shows the routine.
  text = text
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (!trimmed) return false;
      if (/^[-*•]\s/.test(trimmed)) return false;
      if (/^\d{1,2}:\d{2}\s*(AM|PM)?\s*[-–—]/.test(trimmed)) return false;
      if (/^is this what you needed\??$/i.test(trimmed)) return false;
      return true;
    })
    .join("\n")
    .trim();

  return text;
}
