import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  Bot,
  FileJson,
  LayoutGrid,
  Plus,
  Search,
  Trash2,
  Pencil,
  X,
} from "lucide-react";
import { ROUTES } from "../../lib/routes";
import { hubApi, type AgentHubRecord, type SkillRecord } from "../../lib/hubApi";
import { parseN8nWorkflow, type AgentCapabilityInput } from "../../lib/n8nWorkflowParser";
import { getAgentIconStyle } from "./AgentDashboard/agentIcons";
import { CATEGORY_LABELS } from "./AgentDashboard/agentConstants";

type Tab = "all" | "custom";
type CreateMode = "manual" | "n8n";

const CATEGORY_OPTIONS = Object.entries(CATEGORY_LABELS).map(([value, label]) => ({
  value,
  label,
}));

const EMPTY_CAPABILITY: AgentCapabilityInput = { name: "", description: "", tools: [] };

const inputClass =
  "w-full px-3 py-2.5 rounded-xl border border-outline-variant/40 bg-surface-container-lowest text-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30";

const labelClass = "block text-xs font-medium text-on-surface-variant mb-1.5";

function AgentHubCard({
  agent,
  onOpen,
  onDelete,
}: {
  agent: AgentHubRecord;
  onOpen: () => void;
  onDelete?: () => void;
}) {
  const { icon: Icon, iconColor } = getAgentIconStyle(agent.id, agent.category);
  const categoryLabel = CATEGORY_LABELS[agent.category || "general"] ?? agent.category;

  return (
    <li className="min-w-0">
      <button
        type="button"
        onClick={onOpen}
        className="group relative aspect-square w-full rounded-2xl border border-outline-variant/30 bg-surface-container-lowest p-4 flex flex-col transition-all hover:border-primary/30 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
      >
        {agent.kind === "custom" && onDelete && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="absolute top-3 right-3 z-10 p-1.5 rounded-lg text-on-surface-variant/50 opacity-0 group-hover:opacity-100 hover:bg-error/10 hover:text-error transition-all"
            aria-label={`Delete ${agent.name}`}
          >
            <Trash2 size={14} />
          </button>
        )}

        <div
          className={`shrink-0 flex items-center justify-center w-14 h-14 rounded-2xl bg-surface-container-high/80 ${iconColor}`}
        >
          <Icon size={28} />
        </div>

        <div className="flex-1 flex flex-col justify-end mt-3 min-h-0 text-left">
          <p className="text-sm font-semibold text-on-surface line-clamp-2 leading-snug">
            {agent.name}
          </p>

          <div className="flex flex-wrap items-center gap-1 mt-2">
            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary">
              {categoryLabel}
            </span>
            {agent.kind === "custom" && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-surface-container-high text-on-surface-variant">
                Custom
              </span>
            )}
          </div>

          {agent.description && (
            <p className="text-[11px] text-on-surface-variant/75 mt-2 leading-relaxed line-clamp-2">
              {agent.description}
            </p>
          )}

          {(agent.skill_count ?? 0) > 0 && (
            <p className="text-[10px] text-on-surface-variant/60 mt-1.5">
              {agent.skill_count} skill{agent.skill_count === 1 ? "" : "s"}
            </p>
          )}
        </div>
      </button>
    </li>
  );
}

export function AgentHubPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [tab, setTab] = useState<Tab>("all");
  const [agents, setAgents] = useState<AgentHubRecord[]>([]);
  const [skills, setSkills] = useState<SkillRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [createMode, setCreateMode] = useState<CreateMode>("manual");
  const [importError, setImportError] = useState<string | null>(null);
  const [detail, setDetail] = useState<AgentHubRecord | null>(null);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "general",
    system_prompt: "",
    capabilities: [{ ...EMPTY_CAPABILITY }] as AgentCapabilityInput[],
    is_public: false,
  });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const kind = tab === "custom" ? "custom" : undefined;
      const [agentData, skillData] = await Promise.all([
        hubApi.listAgents({ kind, q: q || undefined }),
        hubApi.listSkills({ limit: 200 }),
      ]);
      setAgents(agentData.agents || []);
      setSkills(skillData.skills || []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }, [tab, q]);

  useEffect(() => {
    load();
  }, [load]);

  const stats = useMemo(() => {
    const custom = agents.filter((a) => a.kind === "custom").length;
    return { total: agents.length, custom };
  }, [agents]);

  function resetForm() {
    setForm({
      name: "",
      description: "",
      category: "general",
      system_prompt: "",
      capabilities: [{ ...EMPTY_CAPABILITY }],
      is_public: false,
    });
    setCreateMode("manual");
    setImportError(null);
  }

  function openCreateDialog() {
    resetForm();
    setDialogOpen(true);
  }

  function updateCapability(index: number, patch: Partial<AgentCapabilityInput>) {
    setForm((prev) => ({
      ...prev,
      capabilities: prev.capabilities.map((c, i) => (i === index ? { ...c, ...patch } : c)),
    }));
  }

  function addCapability() {
    setForm((prev) => ({
      ...prev,
      capabilities: [...prev.capabilities, { ...EMPTY_CAPABILITY }],
    }));
  }

  function removeCapability(index: number) {
    setForm((prev) => ({
      ...prev,
      capabilities:
        prev.capabilities.length <= 1
          ? [{ ...EMPTY_CAPABILITY }]
          : prev.capabilities.filter((_, i) => i !== index),
    }));
  }

  function applyN8nImport(raw: unknown) {
    const parsed = parseN8nWorkflow(raw);
    setForm({
      name: parsed.name,
      description: parsed.description,
      category: parsed.category,
      system_prompt: parsed.system_prompt,
      capabilities: parsed.capabilities,
      is_public: false,
    });
    setCreateMode("manual");
    setImportError(null);
  }

  function handleJsonFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const raw = JSON.parse(String(reader.result));
        applyN8nImport(raw);
      } catch (e) {
        setImportError(e instanceof Error ? e.message : "Could not parse workflow JSON");
      }
    };
    reader.readAsText(file);
  }

  const validCapabilities = form.capabilities.filter((c) => c.name.trim());

  async function createAgent() {
    await hubApi.createAgent({
      name: form.name.trim(),
      description: form.description.trim(),
      category: form.category,
      system_prompt: form.system_prompt.trim(),
      capabilities:
        validCapabilities.length > 0
          ? validCapabilities.map((c) => ({
              name: c.name.trim(),
              description: c.description.trim(),
              tools: c.tools,
            }))
          : undefined,
      is_public: form.is_public,
    });
    setDialogOpen(false);
    resetForm();
    await load();
  }

  async function openDetail(agent: AgentHubRecord) {
    if (agent.kind === "custom") {
      const full = await hubApi.getAgent(agent.id);
      setDetail(full);
      setSelectedSkillIds(full.profile?.skill_ids || []);
    } else {
      const profile = await hubApi.getAgentProfile(agent.id);
      setDetail({ ...agent, profile });
      setSelectedSkillIds(profile.skill_ids || []);
    }
  }

  async function saveDetailSkills() {
    if (!detail) return;
    const profile = detail.profile || {
      agent_id: detail.id,
      skill_ids: [],
      ruleset_ids: [],
      extra_system: "",
    };
    await hubApi.putAgentProfile(detail.id, {
      ...profile,
      skill_ids: selectedSkillIds,
    });
    setDetail(null);
    await load();
  }

  async function removeAgent(id: string) {
    if (!confirm("Delete this custom agent?")) return;
    await hubApi.deleteAgent(id);
    await load();
  }

  function toggleSkillId(id: string) {
    setSelectedSkillIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  const detailStyle = detail ? getAgentIconStyle(detail.id, detail.category) : null;
  const DetailIcon = detailStyle?.icon;
  const canCreate =
    form.name.trim() && form.description.trim() && form.system_prompt.trim();

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <header className="border-b border-outline-variant/40 bg-surface-container-lowest/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              to={ROUTES.home}
              className="p-2 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
              aria-label="Back to chat"
            >
              <ArrowLeft size={20} />
            </Link>
            <span className="font-medium text-lg">Agents</span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`${ROUTES.home}?agents=1`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border border-outline-variant/50 hover:bg-surface-container-high transition-colors"
            >
              <LayoutGrid size={14} /> Flow view
            </Link>
            <button
              type="button"
              onClick={openCreateDialog}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-primary text-on-primary"
            >
              <Plus size={14} /> New agent
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="flex items-start gap-4 mb-6">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <Bot size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-medium tracking-tight mb-1">Agent library</h1>
            <p className="text-sm text-on-surface-variant">
              {stats.total} agents · {stats.custom} custom
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <button
            type="button"
            onClick={() => setTab("all")}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              tab === "all"
                ? "bg-primary text-on-primary"
                : "border border-outline-variant/40 text-on-surface-variant hover:bg-surface-container-high"
            }`}
          >
            All agents
          </button>
          <button
            type="button"
            onClick={() => setTab("custom")}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              tab === "custom"
                ? "bg-primary text-on-primary"
                : "border border-outline-variant/40 text-on-surface-variant hover:bg-surface-container-high"
            }`}
          >
            My custom agents
          </button>
        </div>

        <div className="relative mb-6 max-w-md">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60 pointer-events-none"
          />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search agents…"
            className={`${inputClass} pl-9`}
          />
        </div>

        {loading && <p className="text-sm text-on-surface-variant">Loading agents…</p>}
        {error && <p className="text-sm text-error">{error}</p>}

        {!loading && !error && agents.length === 0 && (
          <p className="text-sm text-on-surface-variant">No agents match your filters.</p>
        )}

        <ul className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <AgentHubCard
              key={agent.id}
              agent={agent}
              onOpen={() => openDetail(agent).catch(console.error)}
              onDelete={
                agent.kind === "custom"
                  ? () => removeAgent(agent.id).catch(console.error)
                  : undefined
              }
            />
          ))}
        </ul>
      </main>

      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-surface-container-lowest border border-outline-variant/40 shadow-xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-5 pt-5 pb-3 shrink-0">
              <h2 className="text-lg font-medium">New custom agent</h2>
              <button type="button" onClick={() => setDialogOpen(false)} aria-label="Close">
                <X size={18} />
              </button>
            </div>

            <div className="flex gap-2 px-5 shrink-0">
              <button
                type="button"
                onClick={() => setCreateMode("manual")}
                className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                  createMode === "manual" ? "bg-primary text-on-primary" : "border"
                }`}
              >
                Manual
              </button>
              <button
                type="button"
                onClick={() => setCreateMode("n8n")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                  createMode === "n8n" ? "bg-primary text-on-primary" : "border"
                }`}
              >
                <FileJson size={13} /> Import n8n JSON
              </button>
            </div>

            <div className="overflow-y-auto px-5 py-4 space-y-4 flex-1">
              {createMode === "n8n" ? (
                <div className="rounded-xl border border-dashed border-outline-variant/50 p-6 text-center">
                  <FileJson size={32} className="mx-auto text-primary mb-3" />
                  <p className="text-sm text-on-surface-variant mb-4">
                    Upload an n8n workflow export (.json). We extract the AI Agent prompt, tools, and
                    capabilities automatically — like a Proxmox or API integration agent.
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".json,application/json"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleJsonFile(file);
                      e.target.value = "";
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="px-4 py-2 rounded-xl text-sm bg-primary text-on-primary"
                  >
                    Choose workflow file
                  </button>
                  {importError && <p className="text-xs text-error mt-3">{importError}</p>}
                </div>
              ) : (
                <>
                  <div className="grid sm:grid-cols-2 gap-3">
                    <div>
                      <label className={labelClass}>Name</label>
                      <input
                        value={form.name}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        placeholder="Proxmox Agent"
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Category</label>
                      <select
                        value={form.category}
                        onChange={(e) => setForm({ ...form, category: e.target.value })}
                        className={inputClass}
                      >
                        {CATEGORY_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className={labelClass}>Description</label>
                    <input
                      value={form.description}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                      placeholder="Manages Proxmox VMs via API commands"
                      className={inputClass}
                    />
                  </div>

                  <div>
                    <label className={labelClass}>System prompt</label>
                    <textarea
                      value={form.system_prompt}
                      onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
                      placeholder="You are a Proxmox AI Agent expert designed to generate API commands..."
                      rows={8}
                      className={`${inputClass} font-mono text-xs leading-relaxed`}
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className={labelClass}>Capabilities & tools</label>
                      <button
                        type="button"
                        onClick={addCapability}
                        className="text-xs font-medium text-primary hover:underline"
                      >
                        + Add capability
                      </button>
                    </div>
                    <div className="space-y-2">
                      {form.capabilities.map((cap, index) => (
                        <div
                          key={index}
                          className="grid gap-2 sm:grid-cols-[1fr_1.5fr_auto] items-start rounded-xl border border-outline-variant/30 p-3"
                        >
                          <input
                            value={cap.name}
                            onChange={(e) => updateCapability(index, { name: e.target.value })}
                            placeholder="Tool name"
                            className={inputClass}
                          />
                          <input
                            value={cap.description}
                            onChange={(e) =>
                              updateCapability(index, { description: e.target.value })
                            }
                            placeholder="What this tool does"
                            className={inputClass}
                          />
                          <button
                            type="button"
                            onClick={() => removeCapability(index)}
                            className="p-2 rounded-lg text-on-surface-variant hover:text-error hover:bg-error/10"
                            aria-label="Remove capability"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <label className="flex items-center gap-2 text-sm text-on-surface-variant">
                    <input
                      type="checkbox"
                      checked={form.is_public}
                      onChange={(e) => setForm({ ...form, is_public: e.target.checked })}
                    />
                    Public agent
                  </label>
                </>
              )}
            </div>

            <div className="flex justify-end gap-2 px-5 py-4 border-t border-outline-variant/30 shrink-0">
              <button
                type="button"
                onClick={() => setDialogOpen(false)}
                className="px-4 py-2 rounded-xl text-sm border border-outline-variant/40"
              >
                Cancel
              </button>
              {createMode === "manual" && (
                <button
                  type="button"
                  onClick={() => createAgent().catch(console.error)}
                  disabled={!canCreate}
                  className="px-4 py-2 rounded-xl text-sm bg-primary text-on-primary disabled:opacity-50"
                >
                  Create agent
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {detail && detailStyle && DetailIcon && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-surface-container-lowest border border-outline-variant/40 p-5 shadow-xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4 gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`shrink-0 flex items-center justify-center w-10 h-10 rounded-xl bg-surface-container-high/80 ${detailStyle.iconColor}`}
                >
                  <DetailIcon size={20} />
                </div>
                <h2 className="text-lg font-medium truncate">{detail.name}</h2>
              </div>
              <button type="button" onClick={() => setDetail(null)} aria-label="Close">
                <X size={18} />
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5 mb-3">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary">
                {CATEGORY_LABELS[detail.category || "general"] ?? detail.category}
              </span>
              {detail.kind === "custom" && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-surface-container-high text-on-surface-variant">
                  Custom
                </span>
              )}
            </div>

            <p className="text-sm text-on-surface-variant mb-4">{detail.description}</p>

            {detail.capabilities && detail.capabilities.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium mb-2">Capabilities</h3>
                <ul className="space-y-1.5">
                  {(detail.capabilities as AgentCapabilityInput[]).map((cap, i) => (
                    <li
                      key={i}
                      className="text-xs rounded-lg bg-surface-container-high/50 px-3 py-2"
                    >
                      <span className="font-medium text-on-surface">{cap.name}</span>
                      {cap.description && (
                        <span className="text-on-surface-variant"> — {cap.description}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {detail.kind === "custom" && detail.system_prompt && (
              <div className="mb-4">
                <h3 className="text-sm font-medium mb-2">System prompt</h3>
                <p className="text-xs text-on-surface-variant/70 whitespace-pre-wrap rounded-xl bg-surface-container-high/50 p-3 max-h-40 overflow-y-auto font-mono leading-relaxed">
                  {detail.system_prompt}
                </p>
              </div>
            )}

            <h3 className="text-sm font-medium mb-2">Assigned skills</h3>
            <div className="space-y-2 mb-4 max-h-48 overflow-y-auto">
              {skills.length === 0 ? (
                <p className="text-xs text-on-surface-variant">No skills available yet.</p>
              ) : (
                skills.map((s) => (
                  <label
                    key={s.id}
                    className="flex items-center gap-2 text-sm text-on-surface-variant hover:text-on-surface"
                  >
                    <input
                      type="checkbox"
                      checked={selectedSkillIds.includes(s.id)}
                      onChange={() => toggleSkillId(s.id)}
                    />
                    {s.name}
                  </label>
                ))
              )}
            </div>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDetail(null)}
                className="px-4 py-2 rounded-xl text-sm border border-outline-variant/40"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => saveDetailSkills().catch(console.error)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm bg-primary text-on-primary"
              >
                <Pencil size={14} /> Save skills
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
