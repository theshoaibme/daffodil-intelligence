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
  data: ResponseContentData;
}

export function ResponseContent({ isThinking, data }: ResponseContentProps) {
  // Ultra-polished Gemini-style loading skeleton inside the scroll area
  if (isThinking) {
    return (
      <div className="flex flex-col gap-3.5 w-full animate-pulse select-none py-1 flex-1">
        <div className="h-4 bg-on-surface/10 rounded-full w-[90%]" />
        <div className="h-4 bg-on-surface/10 rounded-full w-[80%]" />
        <div className="h-4 bg-on-surface/10 rounded-full w-[65%]" />
        <div className="flex flex-col gap-3.5 mt-3 pl-4">
          <div className="flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-on-surface/10 flex-shrink-0" />
            <div className="h-3.5 bg-on-surface/10 rounded-full w-[75%]" />
          </div>
          <div className="flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-on-surface/10 flex-shrink-0" />
            <div className="h-3.5 bg-on-surface/10 rounded-full w-[55%]" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-y-auto custom-scrollbar flex-1 pr-1.5 flex flex-col gap-4 text-on-surface text-[13.5px] leading-relaxed font-sans select-text">
      {data.paragraphs.map((p, idx) => (
        <p key={idx} className="font-normal opacity-95">
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
    </div>
  );
}
