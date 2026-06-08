import { useEffect, useState } from "react";
import { Wrench, Sparkles, ListChecks } from "lucide-react";
import type { Agent } from "../../../hooks/useAgents";
import { getAgentIconStyle } from "./agentIcons";
import {
  CATEGORY_DESCRIPTIONS,
  CATEGORY_LABELS,
  resolveAgentDescription,
} from "./agentConstants";

const API_BASE = import.meta.env.VITE_API_URL || "";

export interface SkillInfo {
  id: string;
  name: string;
  description: string;
}

interface AgentProfile {
  skill_ids: string[];
}

const skillsCache = new Map<string, SkillInfo[]>();
let skillCatalogCache: Record<string, SkillInfo> | null = null;

async function loadSkillCatalog(): Promise<Record<string, SkillInfo>> {
  if (skillCatalogCache) return skillCatalogCache;
  const catalog: Record<string, SkillInfo> = {};
  try {
    const res = await fetch(`${API_BASE}/api/skills/`);
    if (res.ok) {
      const data = await res.json();
      for (const skill of data.skills ?? []) {
        catalog[skill.id] = {
          id: skill.id,
          name: skill.name,
          description: skill.description,
        };
      }
    }
  } catch {
    // Skills list may require auth.
  }
  skillCatalogCache = catalog;
  return catalog;
}

async function fetchAgentSkills(agentId: string): Promise<SkillInfo[]> {
  if (skillsCache.has(agentId)) return skillsCache.get(agentId)!;

  const catalog = await loadSkillCatalog();
  try {
    const res = await fetch(`${API_BASE}/api/skills/config/agent/${agentId}`);
    if (!res.ok) {
      skillsCache.set(agentId, []);
      return [];
    }
    const profile = (await res.json()) as AgentProfile;
    const skills = (profile.skill_ids ?? []).map(
      (skillId) => catalog[skillId] ?? { id: skillId, name: skillId, description: "" }
    );
    skillsCache.set(agentId, skills);
    return skills;
  } catch {
    skillsCache.set(agentId, []);
    return [];
  }
}

export function useAgentSkills(agentId: string | null) {
  const [skills, setSkills] = useState<SkillInfo[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!agentId) {
      setSkills([]);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    fetchAgentSkills(agentId).then((result) => {
      if (!cancelled) {
        setSkills(result);
        setLoading(false);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [agentId]);

  return { skills, loading };
}

export function formatToolName(tool: string): string {
  return tool.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function SectionTitle({ icon: Icon, label }: { icon: typeof ListChecks; label: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-1.5">
      <Icon size={12} className="text-primary/70" />
      <h4 className="text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant/70">
        {label}
      </h4>
    </div>
  );
}

export function AgentProfileRow({ agent, size = "md" }: { agent: Agent; size?: "sm" | "md" }) {
  const category = agent.category || "general";
  const { icon: Icon, iconColor } = getAgentIconStyle(agent.id, category);
  const compact = size === "sm";

  return (
    <div className={`flex items-center min-w-0 ${compact ? "gap-2" : "gap-2.5"}`}>
      <div
        className={`rounded-full flex items-center justify-center bg-surface-container-low shrink-0 ${
          compact ? "w-7 h-7" : "w-8 h-8"
        }`}
      >
        <Icon size={compact ? 14 : 16} className={iconColor} />
      </div>
      <div className="min-w-0">
        <h3 className={`font-semibold text-on-surface leading-tight truncate ${compact ? "text-xs" : "text-sm"}`}>
          {agent.name}
        </h3>
        <p className="text-[10px] text-on-surface-variant/65 truncate">
          {CATEGORY_LABELS[category] ?? category}
        </p>
      </div>
    </div>
  );
}

export function AgentDetailContent({
  agent,
  skills,
  loadingSkills = false,
  compact = false,
  showProfile = true,
}: {
  agent: Agent;
  skills: SkillInfo[];
  loadingSkills?: boolean;
  compact?: boolean;
  showProfile?: boolean;
}) {
  const category = agent.category || "general";
  const description = resolveAgentDescription(agent.id, agent.description);
  const categoryDesc = CATEGORY_DESCRIPTIONS[category];
  const tools = agent.tools ?? [];
  const sectionGap = compact ? "space-y-3" : "space-y-4";

  return (
    <div className={sectionGap}>
      {showProfile && <AgentProfileRow agent={agent} size={compact ? "sm" : "md"} />}

      <section className={compact ? "" : "pt-0.5"}>
        <SectionTitle icon={ListChecks} label="Capabilities" />
        <p className="text-[11px] text-on-surface/85 leading-snug">{description}</p>
        {categoryDesc && (
          <p className="text-[10px] text-on-surface-variant/65 mt-1 leading-snug">{categoryDesc}</p>
        )}
      </section>

      <section>
        <SectionTitle icon={Wrench} label="Tools" />
        {tools.length > 0 ? (
          <div className="flex flex-wrap gap-1">
            {tools.map((tool) => (
              <span
                key={tool}
                className="px-1.5 py-px rounded-md text-[10px] font-medium text-primary bg-primary/10 border border-primary/15"
              >
                {formatToolName(tool)}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-on-surface-variant/55">No tools registered.</p>
        )}
      </section>

      <section>
        <SectionTitle icon={Sparkles} label="Skills" />
        {loadingSkills ? (
          <p className="text-[11px] text-on-surface-variant/55">Loading skills…</p>
        ) : skills.length > 0 ? (
          <ul className="space-y-1.5">
            {skills.map((skill) => (
              <li key={skill.id}>
                <p className="text-[11px] font-medium text-on-surface">{skill.name}</p>
                {skill.description && (
                  <p className="text-[10px] text-on-surface-variant/65 mt-px leading-snug">
                    {skill.description}
                  </p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-[11px] text-on-surface-variant/55">No custom skills configured.</p>
        )}
      </section>
    </div>
  );
}
