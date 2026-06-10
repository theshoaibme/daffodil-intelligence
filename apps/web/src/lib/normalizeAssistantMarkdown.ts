import { dedupeRepeatedSections } from "./contentDedupe";

const BOX_CHARS = /[┌┐└┘├┤─│▼]/;
const LANG_TAGS = /\b(bash|python|text|sh|json|typescript|javascript)\b/i;
const FENCE = "```";

/** Normalize model output that collapses markdown onto single lines. */
export function normalizeAssistantMarkdown(raw: string): string {
  let text = dedupeRepeatedSections((raw || "").trim());
  if (!text) return text;

  const { text: withDiagrams, placeholders } = extractAndWrapDiagrams(text);
  text = withDiagrams;

  text = fixInlineHeaders(text);
  text = fixHorizontalRules(text);
  text = fixInlineCodeFences(text);
  text = fixLanguageTaggedBlocks(text);
  text = convertTextInstructionBlocks(text);
  text = formatExamScheduleBlock(text);
  text = sanitizeFenceMarkers(text);
  text = collapseExcessiveNewlines(text);
  text = restoreDiagramPlaceholders(text, placeholders);

  return text.trim();
}

function fixInlineHeaders(text: string): string {
  return text
    .replace(/([^\n#])\s*(#{1,6}\s+)/g, "$1\n\n$2")
    .replace(/(🤖[^\n#]*)\s*(##\s+)/g, "$1\n\n$2");
}

function fixHorizontalRules(text: string): string {
  return text
    .replace(/\s*---\s*(?=##\s)/g, "\n\n---\n\n")
    .replace(/\s*---\s*(?=Step\s*\d)/gi, "\n\n---\n\n")
    .replace(/([^\n-])\s*---\s+([A-Za-z#📅🤖])/g, "$1\n\n---\n\n$2");
}

function fixInlineCodeFences(text: string): string {
  const openFence = new RegExp(FENCE + "(\\w*)\\s*", "g");
  const closeFence = new RegExp("\\s*" + FENCE + "\\s*(?=\\n|$|##|---)", "g");
  let out = text.replace(openFence, (_, lang) => "\n\n" + FENCE + (lang || "") + "\n");
  out = out.replace(closeFence, "\n" + FENCE + "\n");
  return out;
}

function fixLanguageTaggedBlocks(text: string): string {
  let out = text;

  out = out.replace(
    /(##\s*Step\s*\d+:[^\n]*?)\s+(bash|python|sh)\s+(pip\s|import\s|#\s)/gi,
    "$1\n\n" + FENCE + "$2\n$3"
  );

  out = out.replace(
    /(##\s*Step\s*\d+:[^\n]*?)\s+(python)\s+(#\s*\S+\.py)/gi,
    "$1\n\n" + FENCE + "$2\n$3"
  );

  out = out.replace(
    /(^|\n\n)\s*(bash)\s+(pip\s+[^\n]+)/gi,
    "$1" + FENCE + "bash\n$3\n" + FENCE + "\n"
  );

  out = out.replace(/(\})\s*(---|##\s)/g, "$1\n" + FENCE + "\n\n$2");

  return closeTrailingCodeFence(out);
}

/** Turn inline ```text 1. ... 2. ... into a markdown ordered list. */
function convertTextInstructionBlocks(text: string): string {
  let out = text.replace(
    /(##\s*Step\s*\d+:[^\n]*)\n*(?:```\s*)?text\s*((?:\d+\.\s[^\n`]+(?:\s|$))+)/gi,
    (_, heading, steps) => {
      const list = steps
        .trim()
        .replace(/\s+(?=\d+\.\s)/g, "\n")
        .replace(/`{3}\s*$/g, "")
        .replace(/^\s+|\s+$/g, "");
      return `${heading}\n\n${list}`;
    }
  );

  out = out.replace(/(\d+\.\s[^\n]+)\s*`{3}\s*(?=\n|$)/g, "$1");
  return out;
}

function closeTrailingCodeFence(text: string): string {
  const marker = FENCE + "python";
  const start = text.lastIndexOf(marker);
  if (start === -1) return text;
  const tail = text.slice(start + marker.length);
  if (tail.includes(FENCE)) return text;
  return text + "\n" + FENCE;
}

function findDiagramEnd(text: string, start: number): number {
  let depth = 0;
  for (let i = start; i < text.length; i++) {
    const ch = text[i];
    if (ch === "┌") depth++;
    else if (ch === "└") {
      depth--;
      if (depth === 0) return i;
    }
  }
  return -1;
}

function stripAdjacentFences(text: string, start: number, end: number): { text: string; start: number; end: number } {
  let out = text;
  let s = start;
  let e = end;

  const before = out.slice(Math.max(0, s - 24), s);
  const fenceBefore = before.match(/`{3}\s*\w*\s*$/);
  if (fenceBefore) {
    const removeLen = fenceBefore[0].length;
    out = out.slice(0, s - removeLen) + out.slice(s);
    s -= removeLen;
    e -= removeLen;
  }

  const after = out.slice(e + 1, e + 24);
  const fenceAfter = after.match(/^\s*`{3}\s*\w*/);
  if (fenceAfter) {
    out = out.slice(0, e + 1) + out.slice(e + 1 + fenceAfter[0].length);
  }

  return { text: out, start: s, end: e };
}

function extractAndWrapDiagrams(text: string): { text: string; placeholders: string[] } {
  if (!BOX_CHARS.test(text)) return { text, placeholders: [] };

  const placeholders: string[] = [];
  let out = text;
  let searchFrom = 0;

  while (searchFrom < out.length) {
    const start = out.indexOf("┌", searchFrom);
    if (start === -1) break;

    let end = findDiagramEnd(out, start);
    if (end === -1) {
      searchFrom = start + 1;
      continue;
    }

    const stripped = stripAdjacentFences(out, start, end);
    out = stripped.text;
    const s = stripped.start;
    end = stripped.end;

    const raw = out.slice(s, end + 1);
    const expanded = expandDiagramLines(raw);
    const wrapped = "\n\n" + FENCE + "\n" + expanded + "\n" + FENCE + "\n";
    const key = `<<DIAGRAM_${placeholders.length}>>`;
    placeholders.push(wrapped);

    out = out.slice(0, s) + key + out.slice(end + 1);
    searchFrom = s + key.length;
  }

  return { text: out, placeholders };
}

function restoreDiagramPlaceholders(text: string, placeholders: string[]): string {
  let out = text;
  placeholders.forEach((diagram, index) => {
    out = out.replace(`<<DIAGRAM_${index}>>`, diagram);
  });
  return out;
}

function expandDiagramLines(region: string): string {
  const trimmed = region.trim();
  const lineCount = trimmed.split("\n").filter((l) => l.trim()).length;
  if (lineCount >= 3) return trimmed;

  return trimmed
    .replace(/(?<=[┐┘┤│])\s+(?=[┌├│])/g, "\n")
    .replace(/\s+(?=[├└▼])/g, "\n")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .join("\n");
}

function sanitizeFenceMarkers(text: string): string {
  let out = text;

  // Orphan opening fences with no body (e.g. bare ``` or ```text on its own line)
  out = out.replace(/^\s*`{3}\s*\w*\s*$/gim, "");
  out = out.replace(/(\n`{3}\n){2,}/g, "\n```\n");
  out = out.replace(new RegExp(FENCE + "text\\s*\\n", "g"), FENCE + "\n");

  // Inline orphan fences mid-paragraph (common in collapsed model output)
  out = out.replace(/\s+`{3}\s*\w*\s+(?=[┌#\-*])/g, "\n\n");
  out = out.replace(/(?<=[┘\n])\s+`{3}\s*\w*(?=\s|$)/g, "\n");

  // Unpaired fence labels that would render as visible text
  out = out.replace(/(^|\n)\s*`{3}text\s*(?=\n|$)/gi, "$1");

  return out;
}

function formatExamScheduleBlock(text: string): string {
  if (!/📅\s*Upcoming Exam Schedule/i.test(text)) return text;

  let out = text.replace(
    /📅\s*Upcoming Exam Schedule/i,
    "\n\n### 📅 Upcoming Exam Schedule\n"
  );

  out = out.replace(
    /-\s*(CSE\d+):\s*([^\n📅-]+?)\s*📅\s*([^\n📍-]+?)\s*📍\s*([^\n-]+)/gi,
    "\n- **$1**: $2  \n  📅 $3  \n  📍 $4"
  );

  out = out.replace(/💡\s*Tip:/g, "\n\n💡 **Tip:**");

  return out;
}

function collapseExcessiveNewlines(text: string): string {
  return text.replace(/\n{4,}/g, "\n\n\n");
}

export function shouldRenderAsMarkdown(text: string): boolean {
  if (!text.trim()) return false;
  if (MARKDOWN_HINT.test(text)) return true;
  if (/#{1,6}\s+\S/.test(text)) return true;
  if (/\*\*[^*]+\*\*/.test(text)) return true;
  if (/`[^`\n]+`/.test(text)) return true;
  if (BOX_CHARS.test(text)) return true;
  if (/📅|🤖|💡/.test(text)) return true;
  if (LANG_TAGS.test(text) && (text.includes("##") || text.includes(FENCE))) return true;
  if (/\|.+\|/.test(text) && text.includes("\n")) return true;
  return text.length > 500 && text.includes("\n\n");
}

const MARKDOWN_HINT = new RegExp(
  "(^|\\n)\\s{0,3}(#{1,6}\\s|" +
    FENCE +
    "|[-*]\\s|\\d+\\.\\s)|\\*\\*[^*]+\\*\\*|---",
  "m"
);
