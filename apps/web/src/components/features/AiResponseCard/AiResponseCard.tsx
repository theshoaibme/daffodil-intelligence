import { useState, useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { ThinkingProcess, ThinkingStep } from "./ThinkingProcess";
import { ResponseContent } from "./ResponseContent";
import { ActionButtons } from "./ActionButtons";
import { UserMessageBadge } from "./UserMessageBadge";
import { parseResponseText } from "./responseParse";

interface AiResponseCardProps {
  prompt?: string;
  response?: string;
  isStreaming?: boolean;
  thinkingSteps?: ThinkingStep[];
  thinkingText?: string;
  thinkingMs?: number | null;
  isThinking?: boolean;
  onEdit?: () => void;
  error?: string | null;
  fillHeight?: boolean;
  onFullView?: () => void;
}

export function AiResponseCard({ 
  prompt, 
  response = "",
  isStreaming = false,
  thinkingSteps: externalSteps = [],
  thinkingText = "",
  thinkingMs = null,
  isThinking: externalIsThinking = false,
  onEdit,
  error,
  fillHeight = false,
  onFullView,
}: AiResponseCardProps) {
  const [thinkingExpanded, setThinkingExpanded] = useState(true);

  const steps = externalSteps;
  const hasContent = response.trim().length > 0;
  const isThinking = (externalIsThinking || isStreaming) && !hasContent;

  useEffect(() => {
    if (isStreaming) {
      setThinkingExpanded(true);
    } else {
      setThinkingExpanded(false);
    }
  }, [isStreaming, prompt]);

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
          thinkingText={thinkingText}
          thinkingMs={thinkingMs}
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
