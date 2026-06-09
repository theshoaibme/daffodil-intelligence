import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Plus,
  Search,
  Sparkles,
  Trash2,
  Pencil,
  Link2,
  X,
} from "lucide-react";
import { ROUTES } from "@lib";
import { FIELD_CLASS_COMPACT, SELECT_CLASS } from "@lib";
import { hubApi, type AgentHubRecord, type SkillRecord } from "@lib";

type AssignTarget = "global" | string;

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillRecord[]>([]);
  const [stats, setStats] = useState({ count: 0, public_count: 0, copycat_count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [tag, setTag] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [editing, setEditing] = useState<SkillRecord | null>(null);
  const [agents, setAgents] = useState<AgentHubRecord[]>([]);
  const [assignTarget, setAssignTarget] = useState<AssignTarget>("global");
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [form, setForm] = useState({
    name: "",
    description: "",
    content: "",
    tags: "",
    tool_names: "",
    is_public: false,
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await hubApi.listSkills({
        q: q || undefined,
        source: source || undefined,
        tag: tag || undefined,
      });
      setSkills(data.skills ?? []);
      setStats({
        count: data.count ?? 0,
        public_count: data.public_count ?? 0,
        copycat_count: data.copycat_count ?? 0,
      });
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
    } finally {
      setLoading(false);
    }
  }, [q, source, tag]);

  useEffect(() => {
    load();
  }, [load]);

  const allTags = useMemo(() => {
    const set = new Set<string>();
    skills.forEach((s) => (s.tags || []).forEach((t) => set.add(t)));
    return Array.from(set).sort();
  }, [skills]);

  function openCreate() {
    setEditing(null);
    setForm({ name: "", description: "", content: "", tags: "", tool_names: "", is_public: false });
    setDialogOpen(true);
  }

  function openEdit(skill: SkillRecord) {
    setEditing(skill);
    setForm({
      name: skill.name,
      description: skill.description,
      content: skill.content,
      tags: (skill.tags || []).join(", "),
      tool_names: (skill.tool_names || []).join(", "),
      is_public: !!skill.is_public,
    });
    setDialogOpen(true);
  }

  async function saveSkill() {
    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      content: form.content.trim(),
      tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
      tool_names: form.tool_names.split(",").map((t) => t.trim()).filter(Boolean),
      is_public: form.is_public,
    };
    if (editing) {
      await hubApi.updateSkill(editing.id, payload);
    } else {
      await hubApi.createSkill(payload);
    }
    setDialogOpen(false);
    await load();
  }

  async function removeSkill(id: string) {
    if (!confirm("Delete this skill?")) return;
    await hubApi.deleteSkill(id);
    await load();
  }

  async function openAssign() {
    const agentData = await hubApi.listAgents();
    setAgents(agentData.agents || []);
    setAssignOpen(true);
    if (assignTarget === "global") {
      const cfg = await hubApi.getGlobalConfig();
      setSelectedSkillIds(cfg.skill_ids || []);
    } else {
      const profile = await hubApi.getAgentProfile(assignTarget);
      setSelectedSkillIds(profile.skill_ids || []);
    }
  }

  async function saveAssignment() {
    if (assignTarget === "global") {
      const cfg = await hubApi.getGlobalConfig();
      await hubApi.putGlobalConfig({ ...cfg, skill_ids: selectedSkillIds });
    } else {
      const profile = await hubApi.getAgentProfile(assignTarget);
      await hubApi.putAgentProfile(assignTarget, { ...profile, skill_ids: selectedSkillIds });
    }
    setAssignOpen(false);
  }

  function toggleSkillId(id: string) {
    setSelectedSkillIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <header className="border-b border-outline-variant/40 bg-surface-container-lowest/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              to={ROUTES.home}
              className="p-2 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
              aria-label="Back to chat"
            >
              <ArrowLeft size={20} />
            </Link>
            <span className="font-medium text-lg">Skills Hub</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => openAssign().catch(console.error)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border border-outline-variant/50 hover:bg-surface-container-high"
            >
              <Link2 size={14} /> Assign
            </button>
            <button
              type="button"
              onClick={openCreate}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-primary text-on-primary"
            >
              <Plus size={14} /> New skill
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <Sparkles size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-medium tracking-tight mb-1">Skill library</h1>
            <p className="text-sm text-on-surface-variant">
              {stats.count} total · {stats.public_count} public · {stats.copycat_count} copycat
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search skills…"
              className={`${FIELD_CLASS_COMPACT} pl-9`}
            />
          </div>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className={SELECT_CLASS}
          >
            <option value="">All sources</option>
            <option value="manual">Manual</option>
            <option value="copycat">Copycat</option>
            <option value="hub">Hub</option>
          </select>
          <select
            value={tag}
            onChange={(e) => setTag(e.target.value)}
            className={SELECT_CLASS}
          >
            <option value="">All tags</option>
            {allTags.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {loading && <p className="text-sm text-on-surface-variant">Loading skills…</p>}
        {error && <p className="text-sm text-error">{error}</p>}

        {!loading && !error && skills.length === 0 && (
          <p className="text-sm text-on-surface-variant">No skills configured yet.</p>
        )}

        <ul className="grid gap-3 sm:grid-cols-2">
          {skills.map((skill) => (
            <li
              key={skill.id}
              className="rounded-2xl border border-outline-variant/40 bg-surface-container-lowest p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-semibold text-on-surface">{skill.name}</p>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {skill.source && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-surface-container-high text-on-surface-variant">
                        {skill.source}
                      </span>
                    )}
                    {skill.is_public && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary">
                        public
                      </span>
                    )}
                    {(skill.usage_count ?? 0) > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-surface-container-high">
                        {skill.usage_count} uses
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button type="button" onClick={() => openEdit(skill)} className="p-1.5 rounded-lg hover:bg-surface-container-high">
                    <Pencil size={14} />
                  </button>
                  <button type="button" onClick={() => removeSkill(skill.id).catch(console.error)} className="p-1.5 rounded-lg hover:bg-surface-container-high text-error">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              {skill.description && (
                <p className="text-xs text-on-surface-variant/80 mt-2 leading-relaxed line-clamp-3">
                  {skill.description}
                </p>
              )}
              {skill.tags && skill.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {skill.tags.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      </main>

      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/40 p-5 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">{editing ? "Edit skill" : "New skill"}</h2>
              <button type="button" onClick={() => setDialogOpen(false)}><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" className={FIELD_CLASS_COMPACT} />
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Description" className={FIELD_CLASS_COMPACT} />
              <textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} placeholder="Markdown content" rows={6} className={FIELD_CLASS_COMPACT} />
              <input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="Tags (comma-separated)" className={FIELD_CLASS_COMPACT} />
              <input value={form.tool_names} onChange={(e) => setForm({ ...form, tool_names: e.target.value })} placeholder="Tool names (comma-separated)" className={FIELD_CLASS_COMPACT} />
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_public} onChange={(e) => setForm({ ...form, is_public: e.target.checked })} />
                Public skill
              </label>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button type="button" onClick={() => setDialogOpen(false)} className="px-4 py-2 rounded-xl text-sm border">Cancel</button>
              <button type="button" onClick={() => saveSkill().catch(console.error)} className="px-4 py-2 rounded-xl text-sm bg-primary text-on-primary">Save</button>
            </div>
          </div>
        </div>
      )}

      {assignOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/40 p-5 shadow-xl max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">Assign skills</h2>
              <button type="button" onClick={() => setAssignOpen(false)}><X size={18} /></button>
            </div>
            <select
              value={assignTarget}
              onChange={async (e) => {
                const val = e.target.value as AssignTarget;
                setAssignTarget(val);
                if (val === "global") {
                  const cfg = await hubApi.getGlobalConfig();
                  setSelectedSkillIds(cfg.skill_ids || []);
                } else {
                  const profile = await hubApi.getAgentProfile(val);
                  setSelectedSkillIds(profile.skill_ids || []);
                }
              }}
              className={`${FIELD_CLASS_COMPACT} mb-4`}
            >
              <option value="global">Global (all agents)</option>
              {agents.map((a) => (
                <option key={a.id} value={a.id}>{a.name} ({a.kind})</option>
              ))}
            </select>
            <div className="space-y-2">
              {skills.map((s) => (
                <label key={s.id} className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={selectedSkillIds.includes(s.id)} onChange={() => toggleSkillId(s.id)} />
                  {s.name}
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button type="button" onClick={() => setAssignOpen(false)} className="px-4 py-2 rounded-xl text-sm border">Cancel</button>
              <button type="button" onClick={() => saveAssignment().catch(console.error)} className="px-4 py-2 rounded-xl text-sm bg-primary text-on-primary">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
