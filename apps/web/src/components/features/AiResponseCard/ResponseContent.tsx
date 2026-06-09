import { Sparkles } from "lucide-react";

export interface ResponseContentData {
  paragraphs: string[];
  bulletPoints?: Array<{ title: string; desc: string }>;
  specialCta?: {
    text: string;
    actionLabel: string;
  };
}

interface ResponseContentProps {
  isThinking: boolean;
  isStreaming?: boolean;
  data: ResponseContentData;
  variant?: "card" | "chat";
}

function renderFormattedText(text: string) {
  const lines = text.split("\n");
  
  return lines.map((line, lineIdx) => {
    const isBullet = line.trim().startsWith("- ");
    const cleanLine = isBullet ? line.trim().substring(2) : line;
    
    // Process markdown bolds: **text**
    const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
    
    const elements = parts.map((part, partIdx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={partIdx} className="font-semibold text-on-surface">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });

    if (isBullet) {
      return (
        <div key={lineIdx} className="flex gap-2 pl-3 py-0.5">
          <span className="text-on-surface-variant/50 flex-shrink-0">•</span>
          <div className="flex-1 opacity-90">{elements}</div>
        </div>
      );
    }

    return (
      <div key={lineIdx} className="min-h-[1.25rem]">
        {elements}
      </div>
    );
  });
}

export function ResponseContent({
  isThinking,
  isStreaming = false,
  data,
  variant = "card",
}: ResponseContentProps) {
  if (isThinking && data.paragraphs.length === 0) {
    return null;
  }

  const isChat = variant === "chat";

  return (
    <div
      className={`flex flex-col gap-3 text-on-surface text-sm leading-relaxed font-sans select-text ${
        isChat ? "overflow-visible" : "overflow-y-auto no-scrollbar flex-1 pr-1.5 gap-3.5 text-[13.5px]"
      }`}
    >
      {data.paragraphs.map((p, idx) => (
        <div key={idx} className="font-normal opacity-95 flex flex-col gap-1">
          {renderFormattedText(p)}
        </div>
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

      {/* Dynamic Special Interactive Google-Sans CTA Button Option */}
      {data.specialCta && (
        <div className="mt-2.5 p-3 rounded-2xl bg-primary/5 border border-primary/10 flex items-center justify-between gap-3 flex-shrink-0 select-none">
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

      {isStreaming && (
        <span
          className="inline-block w-2 h-4 ml-0.5 bg-primary/70 rounded-sm animate-pulse align-middle"
          aria-hidden
        />
      )}
    </div>
  );
}
