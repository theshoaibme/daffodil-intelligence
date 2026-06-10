const STATUS_LINE =
  /^(Mode:|Model:|Engine:|Fast model selected|Upgraded model for)\b/i;

const SIMULATED_FRAGMENTS = [
  "hmm,",
  "hmm",
  "let me think about that",
  "let me think",
  "okay",
  "alright",
  "considering your question",
  "working through this",
  "one moment",
  "this needs careful reasoning",
  " — this needs careful reasoning",
];

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function stripStatusLines(text: string): string {
  return text
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (!trimmed) return false;
      return !STATUS_LINE.test(trimmed);
    })
    .join("\n");
}

function stripSimulatedFiller(text: string): string {
  let out = text;
  for (const frag of SIMULATED_FRAGMENTS) {
    const pattern = new RegExp(`(${escapeRegExp(frag)}\\s*)+`, "gi");
    out = out.replace(pattern, "");
  }
  return out
    .replace(/\s*[—–-]\s*almost there\.{2,}\s*/gi, "")
    .replace(/(\b\w{3,})\1+/gi, "$1")
    .replace(/\s{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/** Remove runtime metadata and simulated filler from thinking display. */
export function cleanThinkingText(text: string): string {
  if (!text) return "";
  const withoutStatus = stripStatusLines(text);
  return stripSimulatedFiller(withoutStatus).trim();
}

export function hasThinkingContent(text: string): boolean {
  return cleanThinkingText(text).length > 0;
}
