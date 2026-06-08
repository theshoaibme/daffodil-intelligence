import { useEffect, useState } from "react";
import { X, Wrench, Sparkles, ListChecks } from "lucide-react";
import type { Agent } from "../../../hooks/useAgents";
import { getAgentIconStyle } from "./agentIcons";
import {
  CATEGORY_DESCRIPTIONS,
  CATEGORY_LABELS,
  resolveAgentDescription,
} from "./agentConstants";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface SkillInfo {
  id: string;
  name: string;
  description: string;
}

interface AgentProfile {
  skill_ids: string[];
}

interface AgentDetailDialogProps {
  agents: Agent[];
  onClose: () => void;
}

function formatToolName(tool: string): string {
  return tool.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function SectionTitle({ icon: Icon, label }: { icon: typeof ListChecks; label: string }) {
  return (
    <div className="flex items-center gap-2 mb-2.5">
      <Icon size={14} className="text-primary/80" />
      <h4 className="text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant/80">
        {label}
      </h4>
    </div>
  );
}

function AgentDetailPanel({ agent, skills }: { agent: Agent; skills: SkillInfo[] }) {
  const category = agent.category || "general";
  const { icon: Icon, iconColor } = getAgentIconStyle(agent.id, category);
  const description = resolveAgentDescription(agent.id, agent.description);
  const categoryDesc = CATEGORY_DESCRIPTIONS[category];
  const tools = agent.tools ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-11 h-11 rounded-full flex items-center justify-center bg-[#f4f2ff] shrink-0">
          <Icon size={22} className={iconColor} />
        </div>
        <div className="min-w-0">
          <h3 className="text-base font-semibold text-on-surface">{agent.name}</h3>
          <p className="text-xs text-on-surface-variant/70 mt-0.5">
            {CATEGORY_LABELS[category] ?? category}
          </p>
        </div>
      </div>

      <section>
        <SectionTitle icon={ListChecks} label="Capabilities" />
        <p className="text-sm text-on-surface/90 leading-relaxed">{description}</p>
        {categoryDesc && (
          <p className="text-xs text-on-surface-variant/70 mt-2 leading-relaxed">{categoryDesc}</p>
        )}
      </section>

      <section>
        <SectionTitle icon={Wrench} label="Tools" />
        {tools.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {tools.map((tool) => (
              <span
                key={tool}
                className="px-2.5 py-1 rounded-full text-xs font-medium text-primary bg-primary/10"
              >
                {formatToolName(tool)}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-on-surface-variant/60">No tools registered.</p>
        )}
      </section>

      <section>
        <SectionTitle icon={Sparkles} label="Skills" />
        {skills.length > 0 ? (
          <ul className="space-y-3">
            {skills.map((skill) => (
              <li key={skill.id}>
                <p className="text-sm font-medium text-on-surface">{skill.name}</p>
                {skill.description && (
                  <p className="text-xs text-on-surface-variant/70 mt-0.5 leading-relaxed">
                    {skill.description}
                  </p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-on-surface-variant/60">No custom skills configured.</p>
        )}
      </section>
    </div>
  );
}

export function AgentDetailDialog({ agents, onClose }: AgentDetailDialogProps) {
  const [activeId, setActiveId] = useState(agents[0]?.id ?? "");
  const [skillsByAgent, setSkillsByAgent] = useState<Record<string, SkillInfo[]>>({});
  const [loadingSkills, setLoadingSkills] = useState(true);

  useEffect(() => {
    setActiveId(agents[0]?.id ?? "");
  }, [agents]);

  useEffect(() => {
    let cancelled = false;

    async function loadSkills() {
      setLoadingSkills(true);
      const result: Record<string, SkillInfo[]> = {};

      const skillCatalog: Record<string, SkillInfo> = {};
      try {
        const res = await fetch(`${API_BASE}/api/skills/`);
        if (res.ok) {
          const data = await res.json();
          for (const skill of data.skills ?? []) {
            skillCatalog[skill.id] = {
              id: skill.id,
              name: skill.name,
              description: skill.description,
            };
          }
        }
      } catch {
        // Skills list may require auth — fall back to profile IDs only.
      }

      await Promise.all(
        agents.map(async (agent) => {
          try {
            const res = await fetch(`${API_BASE}/api/skills/config/agent/${agent.id}`);
            if (!res.ok) {
              result[agent.id] = [];
              return;
            }
            const profile = (await res.json()) as AgentProfile;
            const ids = profile.skill_ids ?? [];
            result[agent.id] = ids.map(
              (skillId) => skillCatalog[skillId] ?? { id: skillId, name: skillId, description: "" }
            );
          } catch {
            result[agent.id] = [];
          }
        })
      );

      if (!cancelled) {
        setSkillsByAgent(result);
        setLoadingSkills(false);
      }
    }

    loadSkills();
    return () => {
      cancelled = true;
    };
  }, [agents]);

  const activeAgent = agents.find((a) => a.id === activeId) ?? agents[0];
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
          {loadingSkills ? (
            <p className="text-sm text-on-surface-variant/60">Loading skills…</p>
          ) : (
            <AgentDetailPanel agent={activeAgent} skills={skillsByAgent[activeAgent.id] ?? []} />
          )}
        </div>
      </div>
    </div>
  );
}
