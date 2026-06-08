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
    <div className="flex items-center gap-2 mb-2">
      <Icon size={13} className="text-primary/80" />
      <h4 className="text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant/80">
        {label}
      </h4>
    </div>
  );
}

export function AgentDetailContent({
  agent,
  skills,
  loadingSkills = false,
  compact = false,
}: {
  agent: Agent;
  skills: SkillInfo[];
  loadingSkills?: boolean;
  compact?: boolean;
}) {
  const category = agent.category || "general";
  const { icon: Icon, iconColor } = getAgentIconStyle(agent.id, category);
  const description = resolveAgentDescription(agent.id, agent.description);
  const categoryDesc = CATEGORY_DESCRIPTIONS[category];
  const tools = agent.tools ?? [];

  return (
    <div className={compact ? "space-y-4" : "space-y-6"}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-[#f4f2ff] shrink-0">
          <Icon size={20} className={iconColor} />
        </div>
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-on-surface leading-tight">{agent.name}</h3>
          <p className="text-[11px] text-on-surface-variant/70 mt-0.5">
            {CATEGORY_LABELS[category] ?? category}
          </p>
        </div>
      </div>

      <section>
        <SectionTitle icon={ListChecks} label="Capabilities" />
        <p className="text-xs text-on-surface/90 leading-relaxed">{description}</p>
        {categoryDesc && (
          <p className="text-[11px] text-on-surface-variant/70 mt-1.5 leading-relaxed">{categoryDesc}</p>
        )}
      </section>

      <section>
        <SectionTitle icon={Wrench} label="Tools" />
        {tools.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {tools.map((tool) => (
              <span
                key={tool}
                className="px-2 py-0.5 rounded-full text-[10px] font-medium text-primary bg-primary/10"
              >
                {formatToolName(tool)}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-on-surface-variant/60">No tools registered.</p>
        )}
      </section>

      <section>
        <SectionTitle icon={Sparkles} label="Skills" />
        {loadingSkills ? (
          <p className="text-xs text-on-surface-variant/60">Loading skills…</p>
        ) : skills.length > 0 ? (
          <ul className="space-y-2">
            {skills.map((skill) => (
              <li key={skill.id}>
                <p className="text-xs font-medium text-on-surface">{skill.name}</p>
                {skill.description && (
                  <p className="text-[11px] text-on-surface-variant/70 mt-0.5 leading-relaxed">
                    {skill.description}
                  </p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-on-surface-variant/60">No custom skills configured.</p>
        )}
      </section>
    </div>
  );
}
