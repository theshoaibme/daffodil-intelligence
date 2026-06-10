/** Remove legacy simulated-thinking filler without stripping real model thought text. */
export function cleanThinkingText(text: string): string {
  if (!text) return "";
  return text
    .replace(/\s*[—–-]\s*almost there\.{2,}\s*/gi, "")
    .replace(/\.{3,}\s*$/g, "")
    .trimEnd();
}

export function hasThinkingContent(text: string): boolean {
  return cleanThinkingText(text).length > 0 || text.trim().length > 0;
}
