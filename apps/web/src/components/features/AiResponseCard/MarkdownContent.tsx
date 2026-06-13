import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { normalizeAssistantMarkdown } from "@lib/normalizeAssistantMarkdown";

interface MarkdownContentProps {
  content: string;
  isStreaming?: boolean;
  /** Skip re-normalization when parent already sanitized content */
  preNormalized?: boolean;
}

const components: Components = {
  h1: ({ children }) => (
    <h1 className="text-lg font-semibold text-on-surface mt-4 mb-2 first:mt-0 tracking-tight">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-base font-semibold text-on-surface mt-4 mb-1.5 first:mt-0 tracking-tight">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-semibold text-on-surface mt-3 mb-1 first:mt-0">
      {children}
    </h3>
  ),
  p: ({ children }) => (
    <p className="text-[0.9375rem] leading-[1.65] text-on-surface/90 mb-2 last:mb-0">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-5 mb-3 space-y-1 text-[0.9375rem] text-on-surface/90">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-5 mb-3 space-y-1 text-[0.9375rem] text-on-surface/90">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  hr: () => <hr className="my-4 border-0 h-px bg-outline-variant/15" />,
  blockquote: ({ children }) => (
    <blockquote className="my-2 pl-3 text-sm text-on-surface-variant italic border-l border-primary/25">
      {children}
    </blockquote>
  ),
  table: ({ children }) => (
    <div className="my-3 overflow-x-auto rounded-lg bg-surface-container-high/30">
      <table className="w-full text-xs text-left border-collapse">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-surface-container-high/50 text-on-surface">{children}</thead>
  ),
  th: ({ children }) => (
    <th className="px-3 py-2 font-semibold text-on-surface border-b border-outline-variant/15">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-3 py-2 text-on-surface/90 border-b border-outline-variant/10">{children}</td>
  ),
  code: ({ className, children, ...props }) => {
    const isBlock = className?.includes("language-");
    const text = String(children);
    const isDiagram = /[┌┐└┘├┤─│]/.test(text);

    if (isBlock) {
      return (
        <code
          className={`${className ?? ""} ${isDiagram ? "whitespace-pre block" : ""} text-xs font-mono`}
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code
        className="px-1 py-0.5 rounded bg-surface-container-high/80 text-xs font-mono text-primary/90"
        {...props}
      >
        {children}
      </code>
    );
  },
  pre: ({ children }) => {
    const raw = String(
      Array.isArray(children)
        ? children.map((c) => (typeof c === "string" ? c : "")).join("")
        : children ?? ""
    );
    const isDiagram = /[┌┐└┘├┤─│▼]/.test(raw);
    return (
      <pre
        className={
          isDiagram
            ? "my-3 overflow-x-auto rounded-lg bg-surface-container-high/40 px-3 py-2.5 text-[11px] font-mono leading-[1.35] whitespace-pre text-on-surface/85"
            : "my-3 overflow-x-auto rounded-lg bg-surface-container-high/50 px-3 py-2.5 text-xs font-mono leading-relaxed whitespace-pre"
        }
      >
        {children}
      </pre>
    );
  },
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-primary hover:underline break-all"
    >
      {children}
    </a>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-on-surface">{children}</strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
};

export function MarkdownContent({
  content,
  isStreaming = false,
  preNormalized = false,
}: MarkdownContentProps) {
  const normalized = useMemo(
    () => (preNormalized ? content : normalizeAssistantMarkdown(content)),
    [content, preNormalized]
  );

  if (!normalized.trim()) return null;

  return (
    <div className="markdown-body select-text max-w-none text-on-surface">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {normalized}
      </ReactMarkdown>
      {isStreaming ? (
        <span
          className="inline-block w-1.5 h-3.5 ml-0.5 bg-primary/60 rounded-sm animate-pulse align-middle"
          aria-hidden
        />
      ) : null}
    </div>
  );
}
