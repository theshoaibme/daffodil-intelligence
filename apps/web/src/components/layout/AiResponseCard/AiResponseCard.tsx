import { useState, useEffect } from "react";
import { ThinkingProcess, ThinkingStep } from "./ThinkingProcess";
import { ResponseContent, ResponseContentData } from "./ResponseContent";
import { ActionButtons } from "./ActionButtons";
import { UserMessageBadge } from "./UserMessageBadge";

interface AiResponseCardProps {
  prompt?: string;
}

export function AiResponseCard({ prompt }: AiResponseCardProps) {
  const [isThinking, setIsThinking] = useState(true);
  const [thinkingExpanded, setThinkingExpanded] = useState(true);
  const [steps, setSteps] = useState<ThinkingStep[]>([
    { id: "1", title: "Analyzing prompt request context", status: "active" },
    { id: "2", title: "Compiling responsive styling design tokens", status: "pending" },
    { id: "3", title: "Generating responsive grid coordinates", status: "pending" },
  ]);

  // Simulate active step-by-step thinking timeline
  useEffect(() => {
    const timer1 = setTimeout(() => {
      setSteps((prev) =>
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
      setSteps((prev) =>
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
      setSteps((prev) => prev.map((s) => ({ ...s, status: "success" })));
      setIsThinking(false);
      // Auto-collapse thinking process details once thinking completes to let scroll content occupy height
      setThinkingExpanded(false);
    }, 3000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  const responseData: ResponseContentData = {
    paragraphs: [
      "I've integrated the glassmorphic gradient panel aesthetic to perfectly wrap all widgets while adhering to your design guidelines.",
      "The visual system now adapts dynamically to dark/light transitions by computing responsive CSS color mixes."
    ],
    bulletPoints: [
      {
        title: "Adaptive Color Shifting",
        desc: "Fuses hex codes with light/dark variables to render high-contrast charcoal text in light theme and light grey elements in dark theme.",
      },
      {
        title: "Frosting Backdrop Filter",
        desc: "Implements 20px frosted backdrop blurs that dynamically scatter moving dot pattern canvas vectors.",
      },
    ],
    specialCta: {
      text: "Apply System Changes",
      actionLabel: "Glassmorphic Theme Customizer Overlay",
    },
  };

  const textToCopy = `${responseData.paragraphs.join("\n\n")}\n\n${responseData.bulletPoints
    ?.map((b) => `- ${b.title}: ${b.desc}`)
    .join("\n")}`;

  return (
    <div
      className="w-full max-w-md h-[360px] glass-gradient-panel border border-outline-variant/40 rounded-[28px] p-6 shadow-2xl text-left select-none relative overflow-hidden flex flex-col gap-4"
      id="ai-response-card"
    >
      {/* Top Header Row with User Prompt Badge - Full Width */}
      <div className="flex items-center flex-shrink-0 pb-3 border-b border-outline-variant/15 w-full">
        <UserMessageBadge prompt={prompt} />
      </div>

      {/* Accordion Thinking Process List Drawer (Auto expands on send) */}
      <ThinkingProcess
        isThinking={isThinking}
        steps={steps}
        isExpanded={thinkingExpanded}
        onToggleExpand={() => setThinkingExpanded(!thinkingExpanded)}
      />

      {/* Main Dynamic Response Content Area (Scrollable to respect size limits) */}
      <ResponseContent isThinking={isThinking} data={responseData} />

      {/* Action Buttons Panel (Copy, Share, Full View) */}
      {!isThinking && (
        <ActionButtons textToCopy={textToCopy} />
      )}
    </div>
  );
}
