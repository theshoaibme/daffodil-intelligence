import { useState, useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { ThinkingProcess, ThinkingStep } from "./ThinkingProcess";
import { ResponseContent, ResponseContentData } from "./ResponseContent";
import { ActionButtons } from "./ActionButtons";
import { UserMessageBadge } from "./UserMessageBadge";

interface AiResponseCardProps {
  prompt?: string;
  response?: string;
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  isThinking?: boolean;
  onEdit?: () => void;
  error?: string | null;
  fillHeight?: boolean;
}

export function AiResponseCard({ 
  prompt, 
  response = "",
  isStreaming = false,
  thinkingSteps: externalSteps = [],
  isThinking: externalIsThinking = false,
  onEdit,
  error,
  fillHeight = false,
}: AiResponseCardProps) {
  const [thinkingExpanded, setThinkingExpanded] = useState(true);
  
  const [internalSteps, setInternalSteps] = useState<ThinkingStep[]>([]);

  const steps = externalSteps.length > 0 ? externalSteps : internalSteps;
  const hasContent = response.trim().length > 0;
  const isThinking = (externalIsThinking || isStreaming) && !hasContent;

  useEffect(() => {
    setThinkingExpanded(false);
    setInternalSteps([]);
  }, [prompt, response]);

  useEffect(() => {
    if (!isStreaming) {
      setThinkingExpanded(false);
      setInternalSteps([]);
    } else {
      setThinkingExpanded(true);
    }
  }, [isStreaming]);

  useEffect(() => {
    if (isStreaming && externalSteps.length === 0) {
      setInternalSteps([
        { id: "1", title: "Analyzing request", status: "active" },
        { id: "2", title: "Generating response", status: "pending" },
        { id: "3", title: "Finalizing", status: "pending" },
      ]);

      const timer1 = setTimeout(() => {
        setInternalSteps((prev) =>
          prev.map((s) =>
            s.id === "1"
              ? { ...s, status: "success" }
              : s.id === "2"
                ? { ...s, status: "active" }
                : s
          )
        );
      }, 1000);

      const timer2 = setTimeout(() => {
        setInternalSteps((prev) =>
          prev.map((s) =>
            s.id === "2"
              ? { ...s, status: "success" }
              : s.id === "3"
                ? { ...s, status: "active" }
                : s
          )
        );
      }, 2000);

      const timer3 = setTimeout(() => {
        setInternalSteps((prev) => prev.map((s) => ({ ...s, status: "success" })));
      }, 3000);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }
  }, [isStreaming, externalSteps.length]);

  const parseResponse = (text: string): ResponseContentData => {
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
        const lines = trimmed.split("\n").filter(l => l.trim().startsWith("- ") || l.trim().startsWith("* "));
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
  };

  const responseData = parseResponse(response);
  const textToCopy = response;

  return (
    <div
      className={`w-full glass-gradient-panel border border-outline-variant/40 rounded-[28px] p-4 sm:p-6 shadow-md text-left select-none relative overflow-hidden flex flex-col gap-3 sm:gap-4 min-w-0 ${
        fillHeight
          ? "h-full min-h-[200px] max-h-full"
          : "max-w-md h-[min(360px,50dvh)] sm:h-[360px]"
      }`}
      id="ai-response-card"
    >
      {/* Top Header Row with User Prompt Badge - Full Width */}
      <div className="flex items-center flex-shrink-0 pb-3 border-b border-outline-variant/15 w-full">
        <UserMessageBadge prompt={prompt} onEdit={onEdit} />
      </div>

      {/* Accordion Thinking Process List Drawer (Auto expands on send) */}
      <div className="flex-shrink-0 min-w-0">
        <ThinkingProcess
          isThinking={isThinking}
          steps={steps}
          isExpanded={thinkingExpanded}
          onToggleExpand={() => setThinkingExpanded(!thinkingExpanded)}
        />
      </div>

      {/* Main Dynamic Response Content Area (Scrollable to respect size limits) */}
      {error ? (
        <div className="flex-1 min-h-0 flex items-start p-1">
          <div className="flex items-center gap-2 text-error">
            <AlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      ) : (
        <ResponseContent isThinking={isThinking} isStreaming={isStreaming} data={responseData} />
      )}

      {/* Action Buttons Panel (Copy, Share, Full View) */}
      {!isThinking && !error && response && (
        <div className="flex-shrink-0">
          <ActionButtons textToCopy={textToCopy} />
        </div>
      )}
    </div>
  );
}
