import { useEffect, useState } from "react";
import { X } from "lucide-react";
import type { Agent } from "@hooks";
import { AgentDetailContent, AgentProfileRow, useAgentSkills } from "./agentDetailContent";

interface AgentDetailDialogProps {
  agents: Agent[];
  onClose: () => void;
}

export function AgentDetailDialog({ agents, onClose }: AgentDetailDialogProps) {
  const [activeId, setActiveId] = useState(agents[0]?.id ?? "");
  const activeAgent = agents.find((a) => a.id === activeId) ?? agents[0];
  const { skills, loading } = useAgentSkills(activeAgent?.id ?? null);

  useEffect(() => {
    setActiveId(agents[0]?.id ?? "");
  }, [agents]);

  if (!activeAgent) return null;

  const singleAgent = agents.length === 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3">
      <button
        type="button"
        className="absolute inset-0 bg-on-surface/8 backdrop-blur-[3px]"
        aria-label="Close dialog"
        onClick={onClose}
      />

      <div className="relative w-full max-w-sm max-h-[78vh] overflow-hidden rounded-xl border border-outline-variant/25 bg-surface-container-lowest shadow-lg flex flex-col">
        <div className="flex items-center justify-between gap-2 px-3 py-2.5 border-b border-outline-variant/15 bg-surface-container-low/50 shrink-0">
          <div className="min-w-0 flex-1">
            {singleAgent ? (
              <AgentProfileRow agent={activeAgent} size="sm" />
            ) : (
              <>
                <h2 className="text-sm font-semibold text-on-surface">Agent details</h2>
                <p className="text-[10px] text-on-surface-variant/60 mt-px">
                  {agents.length} selected
                </p>
              </>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-on-surface-variant/60 hover:text-on-surface hover:bg-surface-container-high/60 transition-colors shrink-0"
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {!singleAgent && (
          <div className="flex gap-1 px-3 py-2 border-b border-outline-variant/10 overflow-x-auto shrink-0">
            {agents.map((agent) => (
              <button
                key={agent.id}
                type="button"
                onClick={() => setActiveId(agent.id)}
                className={`shrink-0 px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                  activeId === agent.id
                    ? "bg-primary text-white"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-low"
                }`}
              >
                {agent.name}
              </button>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto custom-scrollbar px-3 py-3">
          <AgentDetailContent
            agent={activeAgent}
            skills={skills}
            loadingSkills={loading}
            compact
            showProfile={!singleAgent}
          />
        </div>
      </div>
    </div>
  );
}
