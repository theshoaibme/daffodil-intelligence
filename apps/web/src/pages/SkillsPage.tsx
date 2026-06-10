import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowLeft,
  BookOpen,
  Globe,
  Link2,
  Loader2,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Tag,
  Trash2,
  Wand2,
  X,
} from "lucide-react";
import {
  FIELD_CLASS,
  FIELD_LABEL_CLASS,
  FIELD_PILL_CLASS,
  hubApi,
  ROUTES,
  SELECT_PILL_CLASS,
  TEXTAREA_CLASS,
  type AgentHubRecord,
  type SkillRecord,
} from "@lib";
import { Button } from "@ui";

type AssignTarget = "global" | string;
type SourceFilter = "" | "manual" | "copycat" | "hub";

const SOURCE_OPTIONS: { value: SourceFilter; label: string }[] = [
  { value: "", label: "All" },
  { value: "manual", label: "Manual" },
  { value: "copycat", label: "Copycat" },
  { value: "hub", label: "Hub" },
];

function StatCard({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: typeof Sparkles;
}) {
  return (
    <div className="rounded-2xl border border-outline-variant/30 bg-surface-container-lowest px-4 py-3 min-w-0">
      <div className="flex items-center gap-2 text-on-surface-variant mb-1">
        <Icon size={14} className="shrink-0" />
        <span className="text-xs font-medium truncate">{label}</span>
      </div>
      <p className="text-xl font-semibold text-on-surface tabular-nums">{value}</p>
    </div>
  );
}

function SkillCard({
  skill,
  onEdit,
  onDelete,
}: {
  skill: SkillRecord;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <li className="min-w-0">
      <article className="group relative h-full rounded-2xl border border-outline-variant/30 bg-surface-container-lowest p-4 transition-all hover:border-primary/25 hover:shadow-sm">
        <div className="absolute top-3 right-3 z-10 flex items-center gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 sm:group-focus-within:opacity-100 transition-opacity">
          <button
            type="button"
            onClick={onEdit}
            className="p-1.5 rounded-full border border-outline-variant/30 bg-surface-container-lowest text-on-surface-variant shadow-sm hover:bg-primary/10 hover:text-primary transition-colors"
            aria-label={`Edit ${skill.name}`}
          >
            <Pencil size={13} />
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="p-1.5 rounded-full border border-outline-variant/30 bg-surface-container-lowest text-on-surface-variant shadow-sm hover:bg-error/10 hover:text-error transition-colors"
            aria-label={`Delete ${skill.name}`}
          >
            <Trash2 size={13} />
          </button>
        </div>

        <div className="flex items-start gap-3 pr-16 sm:pr-14">
          <div className="shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-primary/10 text-primary">
            <Wand2 size={18} />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-on-surface truncate leading-tight">
              {skill.name}
            </h3>
            <div className="flex flex-wrap items-center gap-1 mt-1.5">
              {skill.source && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-surface-container-high text-on-surface-variant capitalize">
                  {skill.source}
                </span>
              )}
              {skill.is_public && (
                <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary">
                  <Globe size={10} />
                  Public
                </span>
              )}
              {(skill.usage_count ?? 0) > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-surface-container-high text-on-surface-variant">
                  {skill.usage_count} uses
                </span>
              )}
            </div>
          </div>
        </div>

        {skill.description ? (
          <p className="text-xs text-on-surface-variant/85 mt-3 leading-relaxed line-clamp-2 sm:line-clamp-3">
            {skill.description}
          </p>
        ) : (
          <p className="text-xs text-on-surface-variant/50 mt-3 italic">No description</p>
        )}

        {skill.tags && skill.tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-outline-variant/15">
            {skill.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary"
              >
                <Tag size={9} />
                {tag}
              </span>
            ))}
            {skill.tags.length > 4 && (
              <span className="text-[10px] text-on-surface-variant self-center">
                +{skill.tags.length - 4}
              </span>
            )}
          </div>
        )}
      </article>
    </li>
  );
}

function ModalShell({
  title,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-background/70 backdrop-blur-sm p-0 sm:p-4"
      onClick={onClose}
      role="presentation"
    >
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-labelledby="skills-modal-title"
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 16, scale: 0.98 }}
        transition={{ type: "spring", stiffness: 380, damping: 32 }}
        onClick={(e) => e.stopPropagation()}
        className={`w-full ${wide ? "max-w-xl" : "max-w-lg"} max-h-[92dvh] sm:max-h-[85vh] rounded-t-3xl sm:rounded-2xl bg-surface-container-lowest border border-outline-variant/40 shadow-xl flex flex-col overflow-hidden`}
      >
        <div className="flex items-center justify-between gap-3 px-5 py-4 shrink-0">
          <h2 id="skills-modal-title" className="text-base sm:text-lg font-semibold">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-full hover:bg-surface-container-high text-on-surface-variant border-0 cursor-pointer"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-4">{children}</div>
      </motion.div>
    </motion.div>
  );
}

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillRecord[]>([]);
  const [stats, setStats] = useState({ count: 0, public_count: 0, copycat_count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [source, setSource] = useState<SourceFilter>("");
  const [tag, setTag] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [editing, setEditing] = useState<SkillRecord | null>(null);
  const [agents, setAgents] = useState<AgentHubRecord[]>([]);
  const [assignTarget, setAssignTarget] = useState<AssignTarget>("global");
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [assignSearch, setAssignSearch] = useState("");
  const [saving, setSaving] = useState(false);
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
    skills.forEach((skill) => (skill.tags || []).forEach((value) => set.add(value)));
    return Array.from(set).sort();
  }, [skills]);

  const assignFilteredSkills = useMemo(() => {
    const needle = assignSearch.trim().toLowerCase();
    if (!needle) return skills;
    return skills.filter(
      (skill) =>
        skill.name.toLowerCase().includes(needle) ||
        skill.description?.toLowerCase().includes(needle)
    );
  }, [assignSearch, skills]);

  function openCreate() {
    setEditing(null);
    setForm({
      name: "",
      description: "",
      content: "",
      tags: "",
      tool_names: "",
      is_public: false,
    });
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
    setSaving(true);
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        content: form.content.trim(),
        tags: form.tags
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        tool_names: form.tool_names
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        is_public: form.is_public,
      };
      if (editing) {
        await hubApi.updateSkill(editing.id, payload);
      } else {
        await hubApi.createSkill(payload);
      }
      setDialogOpen(false);
      await load();
    } finally {
      setSaving(false);
    }
  }

  async function removeSkill(id: string) {
    if (!confirm("Delete this skill?")) return;
    await hubApi.deleteSkill(id);
    await load();
  }

  async function openAssign() {
    const agentData = await hubApi.listAgents();
    setAgents(agentData.agents || []);
    setAssignSearch("");
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
    setSaving(true);
    try {
      if (assignTarget === "global") {
        const cfg = await hubApi.getGlobalConfig();
        await hubApi.putGlobalConfig({ ...cfg, skill_ids: selectedSkillIds });
      } else {
        const profile = await hubApi.getAgentProfile(assignTarget);
        await hubApi.putAgentProfile(assignTarget, { ...profile, skill_ids: selectedSkillIds });
      }
      setAssignOpen(false);
    } finally {
      setSaving(false);
    }
  }

  function toggleSkillId(id: string) {
    setSelectedSkillIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id]
    );
  }

  const canSaveSkill = form.name.trim() && form.content.trim();

  return (
    <div className="relative h-[100dvh] text-on-surface font-sans overflow-hidden bg-background">
      <main className="absolute inset-0 z-10 overflow-y-auto no-scrollbar w-full">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-6">
          <div className="h-14 shrink-0" aria-hidden="true" />

          <section className="pt-6 sm:pt-8">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
              <div className="flex items-start gap-4 min-w-0">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary shrink-0">
                  <Sparkles size={24} />
                </div>
                <div className="min-w-0">
                  <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">Skill library</h1>
                  <p className="text-sm text-on-surface-variant mt-1 max-w-xl">
                    Reusable prompts and playbooks you can attach to agents or use globally.
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 sm:shrink-0">
                <button
                  type="button"
                  onClick={() => openAssign().catch(console.error)}
                  className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium border border-outline-variant/50 hover:bg-surface-container-high transition-colors"
                >
                  <Link2 size={14} />
                  Assign
                </button>
                <button
                  type="button"
                  onClick={openCreate}
                  className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium bg-primary text-on-primary hover:opacity-95 transition-opacity"
                >
                  <Plus size={14} />
                  New skill
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 sm:gap-3 mb-6">
              <StatCard label="Total skills" value={stats.count} icon={BookOpen} />
              <StatCard label="Public" value={stats.public_count} icon={Globe} />
              <StatCard label="Copycat" value={stats.copycat_count} icon={Wand2} />
            </div>

            <div className="space-y-3 mb-6">
              <div className="relative w-full">
                <Search
                  size={16}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant/60 pointer-events-none"
                />
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search skills…"
                  className={`${FIELD_PILL_CLASS} pl-10`}
                />
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="flex flex-wrap gap-1.5">
                  {SOURCE_OPTIONS.map((option) => (
                    <button
                      key={option.value || "all"}
                      type="button"
                      onClick={() => setSource(option.value)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                        source === option.value
                          ? "bg-primary text-on-primary"
                          : "border border-outline-variant/40 text-on-surface-variant hover:bg-surface-container-high"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>

                {allTags.length > 0 && (
                  <div className="flex items-center gap-2 min-w-0 sm:ml-auto sm:max-w-xs w-full sm:w-auto">
                    <Tag size={14} className="text-on-surface-variant shrink-0 hidden sm:block" />
                    <select
                      value={tag}
                      onChange={(e) => setTag(e.target.value)}
                      className={`${SELECT_PILL_CLASS} min-w-0 flex-1`}
                      aria-label="Filter by tag"
                    >
                      <option value="">All tags</option>
                      {allTags.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>

            {loading && (
              <div className="flex items-center justify-center gap-2 py-16 text-sm text-on-surface-variant">
                <Loader2 size={18} className="animate-spin" />
                Loading skills…
              </div>
            )}

            {error && (
              <div className="rounded-2xl border border-error/30 bg-error/5 px-4 py-3 text-sm text-error mb-4">
                {error}
              </div>
            )}

            {!loading && !error && skills.length === 0 && (
              <div className="rounded-2xl border border-dashed border-outline-variant/40 bg-surface-container-lowest/50 px-6 py-12 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary/10 text-primary mb-4">
                  <Sparkles size={22} />
                </div>
                <p className="text-sm font-medium text-on-surface mb-1">No skills yet</p>
                <p className="text-xs text-on-surface-variant mb-5 max-w-sm mx-auto">
                  Create a skill to save instructions, workflows, or copycat recordings for your agents.
                </p>
                <button
                  type="button"
                  onClick={openCreate}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium bg-primary text-on-primary"
                >
                  <Plus size={14} />
                  Create your first skill
                </button>
              </div>
            )}

            {!loading && !error && skills.length > 0 && (
              <ul className="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                {skills.map((skill) => (
                  <SkillCard
                    key={skill.id}
                    skill={skill}
                    onEdit={() => openEdit(skill)}
                    onDelete={() => removeSkill(skill.id).catch(console.error)}
                  />
                ))}
              </ul>
            )}
          </section>
        </div>
      </main>

      <header className="absolute top-0 inset-x-0 z-20 w-full bg-transparent pointer-events-none">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-3 pointer-events-auto">
          <div className="flex items-center gap-3 min-w-0">
            <Link
              to={ROUTES.home}
              className="p-2 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors shrink-0"
              aria-label="Back to chat"
            >
              <ArrowLeft size={20} />
            </Link>
            <span className="font-medium text-base sm:text-lg truncate">Skills</span>
          </div>
          <div className="flex items-center gap-2 sm:hidden">
            <button
              type="button"
              onClick={() => openAssign().catch(console.error)}
              className="p-2 rounded-full border border-outline-variant/40 text-on-surface-variant"
              aria-label="Assign skills"
            >
              <Link2 size={16} />
            </button>
            <button
              type="button"
              onClick={openCreate}
              className="p-2 rounded-full bg-primary text-on-primary"
              aria-label="New skill"
            >
              <Plus size={16} />
            </button>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {dialogOpen && (
          <ModalShell
            title={editing ? "Edit skill" : "New skill"}
            onClose={() => setDialogOpen(false)}
            wide
          >
            <div className="space-y-4">
              <div>
                <label htmlFor="skill-name" className={FIELD_LABEL_CLASS}>
                  Name
                </label>
                <input
                  id="skill-name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Thesis outline"
                  className={FIELD_CLASS}
                />
              </div>
              <div>
                <label htmlFor="skill-description" className={FIELD_LABEL_CLASS}>
                  Description
                </label>
                <input
                  id="skill-description"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  placeholder="Short summary for the library"
                  className={FIELD_CLASS}
                />
              </div>
              <div>
                <label htmlFor="skill-content" className={FIELD_LABEL_CLASS}>
                  Content
                </label>
                <textarea
                  id="skill-content"
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  placeholder="Markdown instructions for the agent"
                  rows={8}
                  className={TEXTAREA_CLASS}
                />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="skill-tags" className={FIELD_LABEL_CLASS}>
                    Tags
                  </label>
                  <input
                    id="skill-tags"
                    value={form.tags}
                    onChange={(e) => setForm({ ...form, tags: e.target.value })}
                    placeholder="research, writing"
                    className={FIELD_CLASS}
                  />
                </div>
                <div>
                  <label htmlFor="skill-tools" className={FIELD_LABEL_CLASS}>
                    Tool names
                  </label>
                  <input
                    id="skill-tools"
                    value={form.tool_names}
                    onChange={(e) => setForm({ ...form, tool_names: e.target.value })}
                    placeholder="browser, memory"
                    className={FIELD_CLASS}
                  />
                </div>
              </div>
              <label className="flex items-center gap-2.5 text-sm cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={form.is_public}
                  onChange={(e) => setForm({ ...form, is_public: e.target.checked })}
                  className="rounded border-outline-variant/50"
                />
                <span>Make this skill public</span>
              </label>
            </div>
            <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 mt-6 pt-2">
              <Button type="button" variant="text" size="sm" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                loading={saving}
                disabled={!canSaveSkill}
                onClick={() => saveSkill().catch(console.error)}
              >
                Save skill
              </Button>
            </div>
          </ModalShell>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {assignOpen && (
          <ModalShell title="Assign skills" onClose={() => setAssignOpen(false)} wide>
            <div className="space-y-4">
              <div>
                <label htmlFor="assign-target" className={FIELD_LABEL_CLASS}>
                  Assign to
                </label>
                <select
                  id="assign-target"
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
                  className={FIELD_CLASS}
                >
                  <option value="global">Global (all agents)</option>
                  {agents.map((agent) => (
                    <option key={agent.id} value={agent.id}>
                      {agent.name} ({agent.kind})
                    </option>
                  ))}
                </select>
              </div>

              <div className="relative">
                <Search
                  size={14}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60"
                />
                <input
                  value={assignSearch}
                  onChange={(e) => setAssignSearch(e.target.value)}
                  placeholder="Search skills to assign…"
                  className={`${FIELD_CLASS} pl-9`}
                />
              </div>

              <p className="text-xs text-on-surface-variant">
                {selectedSkillIds.length} selected
              </p>

              <div className="space-y-1 max-h-[min(320px,40dvh)] overflow-y-auto custom-scrollbar rounded-xl border border-outline-variant/25 p-2">
                {assignFilteredSkills.length === 0 ? (
                  <p className="text-sm text-on-surface-variant px-2 py-4 text-center">
                    No skills match your search.
                  </p>
                ) : (
                  assignFilteredSkills.map((skill) => {
                    const checked = selectedSkillIds.includes(skill.id);
                    return (
                      <label
                        key={skill.id}
                        className={`flex items-start gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                          checked ? "bg-primary/10" : "hover:bg-surface-container-high/60"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleSkillId(skill.id)}
                          className="mt-0.5 rounded border-outline-variant/50"
                        />
                        <span className="min-w-0">
                          <span className="text-sm font-medium text-on-surface block truncate">
                            {skill.name}
                          </span>
                          {skill.description && (
                            <span className="text-xs text-on-surface-variant line-clamp-1">
                              {skill.description}
                            </span>
                          )}
                        </span>
                      </label>
                    );
                  })
                )}
              </div>
            </div>
            <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 mt-6 pt-2">
              <Button type="button" variant="text" size="sm" onClick={() => setAssignOpen(false)}>
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                loading={saving}
                onClick={() => saveAssignment().catch(console.error)}
              >
                Save assignment
              </Button>
            </div>
          </ModalShell>
        )}
      </AnimatePresence>
    </div>
  );
}
