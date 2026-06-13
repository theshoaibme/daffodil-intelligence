import { Sparkles } from "lucide-react";
import { shouldRenderAsMarkdown } from "@lib/normalizeAssistantMarkdown";
import { MarkdownContent } from "./MarkdownContent";

export interface ResponseContentData {
  paragraphs: string[];
  bulletPoints?: Array<{ title: string; desc: string }>;
  specialCta?: {
    text: string;
    actionLabel: string;
  };
  /** Full raw text for markdown rendering */
  rawText?: string;
}

interface ResponseContentProps {
  isThinking: boolean;
  isStreaming?: boolean;
  data: ResponseContentData;
  variant?: "card" | "chat";
  /** Content was already normalized in sanitizeAssistantContent */
  preNormalized?: boolean;
}

export function ResponseContent({
  isThinking,
  isStreaming = false,
  data,
  variant = "card",
  preNormalized = false,
}: ResponseContentProps) {
  if (isThinking && data.paragraphs.length === 0) {
    return null;
  }

  const isChat = variant === "chat";
  const rawText = data.rawText ?? data.paragraphs.join("\n\n");
  const useMarkdown = !isStreaming && shouldRenderAsMarkdown(rawText);

  if (isStreaming && rawText) {
    return (
      <div
        className={`flex flex-col gap-3 text-on-surface text-sm leading-relaxed font-sans select-text ${
          isChat ? "overflow-visible" : "overflow-y-auto no-scrollbar flex-1 pr-1.5"
        }`}
      >
        <p className="text-[0.9375rem] leading-[1.65] text-on-surface/90 whitespace-pre-wrap break-words font-normal">
          {rawText}
          <span
            className="inline-block w-1.5 h-3.5 ml-0.5 bg-primary/60 rounded-sm animate-pulse align-middle"
            aria-hidden
          />
        </p>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col gap-3 text-on-surface text-sm leading-relaxed font-sans select-text ${
        isChat ? "overflow-visible" : "overflow-y-auto no-scrollbar flex-1 pr-1.5 gap-3.5 text-[13.5px]"
      }`}
    >
      {useMarkdown ? (
        <MarkdownContent
          content={rawText}
          isStreaming={isStreaming}
          preNormalized={preNormalized}
        />
      ) : (
        <>
          {data.paragraphs.map((p, idx) => (
            <p key={idx} className="font-normal opacity-95 whitespace-pre-wrap">
              {p}
            </p>
          ))}
          {data.bulletPoints && data.bulletPoints.length > 0 && (
            <ul className="list-disc pl-5 flex flex-col gap-3.5">
              {data.bulletPoints.map((item, idx) => (
                <li key={idx} className="marker:text-on-surface-variant/40">
                  <span className="font-semibold text-on-surface">{item.title}:</span>{" "}
                  <span className="opacity-90">{item.desc}</span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {/* Dynamic Special Interactive Google-Sans CTA Button Option */}
      {data.specialCta && (
        <div className="mt-2.5 p-3 rounded-lg bg-primary/5 flex items-center justify-between gap-3 flex-shrink-0 select-none">
          <div className="flex items-center gap-2 text-primary font-medium text-xs">
            <Sparkles size={14} className="animate-pulse" />
            <span>Ready to apply changes?</span>
          </div>
          <button
            onClick={() => alert(`Applying: ${data.specialCta?.actionLabel}`)}
            className="px-4 py-2 rounded-full bg-primary hover:bg-primary-container text-white hover:text-on-primary-container text-xs font-semibold shadow-sm transition-all duration-200 cursor-pointer border-0 outline-none"
          >
            {data.specialCta.text}
          </button>
        </div>
      )}

      {isStreaming && !useMarkdown ? (
        <span
          className="inline-block w-2 h-4 ml-0.5 bg-primary/70 rounded-sm animate-pulse align-middle"
          aria-hidden
        />
      ) : null}
    </div>
  );
}
