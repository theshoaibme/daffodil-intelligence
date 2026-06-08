import { useEffect, useState } from "react";
import { X } from "lucide-react";
import type { Agent } from "../../../hooks/useAgents";
import { AgentDetailContent, useAgentSkills } from "./agentDetailContent";

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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/20 backdrop-blur-sm"
        aria-label="Close dialog"
        onClick={onClose}
      />

      <div className="relative w-full max-w-md max-h-[85vh] overflow-hidden rounded-2xl bg-white shadow-2xl flex flex-col">
        <div className="flex items-start justify-between gap-3 px-5 pt-5 pb-3">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-on-surface">Agent details</h2>
            {agents.length > 1 && (
              <p className="text-xs text-on-surface-variant/70 mt-0.5">
                {agents.length} agents selected
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-full text-on-surface-variant/70 hover:text-on-surface hover:bg-[#f4f2ff] transition-colors shrink-0"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {agents.length > 1 && (
          <div className="flex gap-1.5 px-5 pb-3 overflow-x-auto">
            {agents.map((agent) => (
              <button
                key={agent.id}
                type="button"
                onClick={() => setActiveId(agent.id)}
                className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                  activeId === agent.id
                    ? "bg-primary text-white"
                    : "text-on-surface-variant hover:text-on-surface hover:bg-[#f4f2ff]"
                }`}
              >
                {agent.name}
              </button>
            ))}
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-5 pb-5">
          <AgentDetailContent agent={activeAgent} skills={skills} loadingSkills={loading} />
        </div>
      </div>
    </div>
  );
}
