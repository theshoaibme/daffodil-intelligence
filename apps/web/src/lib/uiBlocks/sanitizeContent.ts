import type { UiBlock } from "./types";

const TOOL_CALL_LINE = /^\s*[a-z][a-z0-9_]*\s*\([^)]*\)\s*$/i;
const TOOL_CALL_INLINE = /\b[a-z][a-z0-9_]*\s*\([^)]*\)/gi;
const COURSE_CODE = /\b[A-Z]{2,4}\d{3}\b/i;

function normalize(text: string): string {
  return text.toLowerCase().replace(/\s+/g, " ").trim();
}

function collectBlockText(blocks: UiBlock[]): string {
  const parts: string[] = [];

  const walkRows = (rows: unknown) => {
    if (!Array.isArray(rows)) return;
    for (const row of rows) {
      if (row && typeof row === "object") {
        parts.push(...Object.values(row as Record<string, unknown>).map(String));
      }
    }
  };

  for (const block of blocks) {
    const data = block.data ?? {};
    if (block.schema === "data_table") {
      walkRows(data.rows);
      if (data.title) parts.push(String(data.title));
    } else if (block.schema === "tabs") {
      const tabs = data.tabs as Array<{ block?: UiBlock }> | undefined;
      for (const tab of tabs ?? []) {
        const inner = tab.block;
        if (!inner?.data) continue;
        walkRows(inner.data.rows);
        if (inner.title) parts.push(String(inner.title));
      }
    }
  }

  return parts.join(" ");
}

function hasStructuredDataBlocks(blocks: UiBlock[]): boolean {
  return blocks.some((block) => {
    if (block.schema === "data_table") {
      const rows = block.data?.rows;
      return Array.isArray(rows) && rows.length > 0;
    }
    if (block.schema === "tabs") {
      const tabs = block.data?.tabs;
      return Array.isArray(tabs) && tabs.length > 0;
    }
    return false;
  });
}

function contentRedundantWithBlocks(content: string, blocks: UiBlock[]): boolean {
  const text = content.trim();
  if (!text) return false;

  const blob = collectBlockText(blocks);
  if (!blob.trim()) return false;

  const normText = normalize(text);
  const normBlob = normalize(blob);

  if (normText.includes(normBlob) || normBlob.includes(normText)) {
    return true;
  }

  const codeMatch = text.match(COURSE_CODE);
  if (codeMatch && blob.toUpperCase().includes(codeMatch[0].toUpperCase())) {
    const scheduleHints = ["room", "sunday", "monday", "tuesday", "am", "pm", "—", "-"];
    if (scheduleHints.some((h) => normText.includes(h))) {
      return true;
    }
  }

  const textWords = new Set(
    normText.match(/[a-z0-9]+/g)?.filter((w) => w.length > 2) ?? []
  );
  const blobWords = new Set(normBlob.match(/[a-z0-9]+/g) ?? []);
  if (textWords.size > 0 && textWords.size <= 12 && [...textWords].every((w) => blobWords.has(w))) {
    return true;
  }

  return false;
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

  if (!hasStructuredDataBlocks(blocks)) {
    return text;
  }

  if (contentRedundantWithBlocks(text, blocks)) {
    return "";
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
      if (contentRedundantWithBlocks(trimmed, blocks)) return false;
      return true;
    })
    .join("\n")
    .trim();

  return text;
}
