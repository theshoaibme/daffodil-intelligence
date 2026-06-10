import type { ResponseContentData } from "./ResponseContent";

export function parseResponseText(text: string): ResponseContentData {
  if (!text) {
    return { paragraphs: [], bulletPoints: [] };
  }

  const paragraphs: string[] = [];
  const bulletPoints: Array<{ title: string; desc: string }> = [];

  const blocks = text.split(/\n\n+/);

  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const lines = trimmed.split("\n").filter((l) => l.trim().startsWith("- ") || l.trim().startsWith("* "));
      for (const line of lines) {
        const match = line.match(/^[-*]\s+(.+?):\s*(.+)$/);
        if (match) {
          bulletPoints.push({ title: match[1], desc: match[2] });
        }
      }
    } else {
      paragraphs.push(trimmed);
    }
  }

  if (paragraphs.length === 0 && text) {
    paragraphs.push(text);
  }

  return { paragraphs, bulletPoints: bulletPoints.length > 0 ? bulletPoints : undefined };
}
