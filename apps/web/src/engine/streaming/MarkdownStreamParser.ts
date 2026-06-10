export interface MarkdownBlock {
  type: "prose" | "code" | "partial";
  content: string;
  lang?: string;
  complete: boolean;
}

interface FenceSegment {
  text: string;
  lang?: string;
  complete: boolean;
}

function splitByCodeFences(raw: string): FenceSegment[] {
  const segments: FenceSegment[] = [];
  const fenceRe = /```(\w*)\n?([\s\S]*?)(```|$)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = fenceRe.exec(raw)) !== null) {
    if (match.index > lastIndex) {
      segments.push({
        text: raw.slice(lastIndex, match.index),
        complete: true,
      });
    }
    const closed = match[0].endsWith("```");
    segments.push({
      text: match[2] ?? "",
      lang: match[1] || undefined,
      complete: closed,
    });
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < raw.length) {
    const tail = raw.slice(lastIndex);
    if (tail.includes("```")) {
      const openIdx = tail.indexOf("```");
      if (openIdx > 0) {
        segments.push({ text: tail.slice(0, openIdx), complete: true });
      }
      const rest = tail.slice(openIdx);
      const langMatch = rest.match(/^```(\w*)\n?([\s\S]*)$/);
      segments.push({
        text: langMatch?.[2] ?? "",
        lang: langMatch?.[1] || undefined,
        complete: false,
      });
    } else {
      segments.push({ text: tail, complete: !tail.includes("```") });
    }
  }

  if (!segments.length) {
    segments.push({ text: raw, complete: !raw.includes("```") });
  }

  return segments;
}

export function parseIncremental(raw: string): MarkdownBlock[] {
  return splitByCodeFences(raw).map((seg) => {
    if (seg.lang !== undefined) {
      return {
        type: seg.complete ? "code" : "partial",
        content: seg.text,
        lang: seg.lang,
        complete: seg.complete,
      };
    }
    return {
      type: seg.complete ? "prose" : "partial",
      content: seg.text,
      complete: seg.complete,
    };
  });
}

export class MarkdownStreamParser {
  private raw = "";

  append(text: string) {
    this.raw += text;
  }

  reset() {
    this.raw = "";
  }

  getBlocks(): MarkdownBlock[] {
    return parseIncremental(this.raw);
  }

  get rawText() {
    return this.raw;
  }
}
