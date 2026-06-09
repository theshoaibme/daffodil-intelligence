import { useCallback, useEffect, useState } from "react";
import { Brain, Loader2, Plus, Search, Trash2 } from "lucide-react";
import { useMemory, MemoryTab } from "../../hooks/useMemory";
import { hubApi, AgentHubRecord } from "../../lib/hubApi";
import { FIELD_CLASS, TEXTAREA_CLASS } from "../../lib/formStyles";

const TABS: { id: MemoryTab; label: string }[] = [
  { id: "facts", label: "Facts" },
  { id: "conversations", label: "Conversations" },
  { id: "configuration", label: "Configuration" },
  { id: "subagents", label: "Sub-agents" },
];

function pillClass(active: boolean) {
  return `px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
    active
      ? "bg-primary text-on-primary"
      : "border border-outline-variant/40 text-on-surface-variant hover:bg-surface-container-high"
  }`;
}

export function MemorySettingsSection() {
  const [tab, setTab] = useState<MemoryTab>("facts");
  const [agentId, setAgentId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [agents, setAgents] = useState<AgentHubRecord[]>([]);
  const [newNote, setNewNote] = useState("");
  const [adding, setAdding] = useState(false);

  const {
    items,
    stats,
    loading,
    error,
    addMemory,
    deleteMemory,
    clearScoped,
    consolidate,
  } = useMemory(tab, agentId || undefined, search || undefined);

  useEffect(() => {
    hubApi
      .listAgents()
      .then((res) => setAgents(res.agents || []))
      .catch(() => setAgents([]));
  }, []);

  const handleAdd = useCallback(async () => {
    if (!newNote.trim()) return;
    setAdding(true);
    try {
      await addMemory(newNote.trim(), tab === "facts" ? "fact" : "episode");
      setNewNote("");
    } finally {
      setAdding(false);
    }
  }, [addMemory, newNote, tab]);

  const readOnly = tab === "configuration";

  return (
    <section className="rounded-2xl border border-outline-variant/40 bg-surface-container-lowest px-5 sm:px-6 py-5">
      <div className="flex items-center justify-between gap-4 mb-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Brain size={18} className="text-primary" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-on-surface">Agent memory</h2>
            {stats && (
              <p className="text-xs text-on-surface-variant mt-0.5">
                {stats.total} memories
                {stats.qdrant_available ? " · Qdrant active" : " · keyword fallback"}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {TABS.map((t) => (
          <button key={t.id} type="button" onClick={() => setTab(t.id)} className={pillClass(tab === t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <select
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
          className={`${FIELD_CLASS} sm:max-w-[200px]`}
        >
          <option value="">All agents</option>
          <option value="main">main</option>
          {agents.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name}
            </option>
          ))}
        </select>
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search memories..."
            className={`${FIELD_CLASS} pl-9`}
          />
        </div>
      </div>

      {tab === "facts" && (
        <div className="mb-4 flex gap-2">
          <textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Add a fact or preference..."
            rows={2}
            className={`${TEXTAREA_CLASS} flex-1`}
          />
          <button
            type="button"
            onClick={handleAdd}
            disabled={adding || !newNote.trim()}
            className="self-end px-4 py-2.5 rounded-full bg-primary text-on-primary text-sm font-semibold disabled:opacity-50"
          >
            {adding ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          </button>
        </div>
      )}

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          onClick={() => clearScoped({ memory_type: tab === "facts" ? "fact" : undefined })}
          className="text-xs font-medium text-on-surface-variant hover:text-error"
        >
          Clear scoped
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Clear ALL memories? This cannot be undone.")) {
              clearScoped({ all: true });
            }
          }}
          className="text-xs font-medium text-error hover:underline"
        >
          Clear all
        </button>
        {tab === "subagents" && (
          <button
            type="button"
            onClick={consolidate}
            className="text-xs font-medium text-primary hover:underline"
          >
            Consolidate sub-agents
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-on-surface-variant py-6">
          <Loader2 size={16} className="animate-spin" />
          Loading memories...
        </div>
      )}

      {error && (
        <p className="text-sm text-error py-2" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && items.length === 0 && (
        <p className="text-sm text-on-surface-variant py-4">No memories in this category yet.</p>
      )}

      <ul className="space-y-2 max-h-[360px] overflow-y-auto">
        {items.map((item) => (
          <li
            key={item.id}
            className="rounded-xl border border-outline-variant/30 bg-surface-container-low px-3 py-2.5"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5 mb-1">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-primary/80">
                    {item.memory_type}
                  </span>
                  <span className="text-[10px] text-on-surface-variant">{item.agent_id}</span>
                </div>
                <p className="text-sm text-on-surface whitespace-pre-wrap break-words line-clamp-4">
                  {item.content}
                </p>
                {item.created_at && (
                  <p className="text-[10px] text-on-surface-variant/70 mt-1">
                    {new Date(item.created_at).toLocaleString()}
                  </p>
                )}
              </div>
              {!readOnly && (
                <button
                  type="button"
                  onClick={() => deleteMemory(item.id)}
                  className="p-1.5 rounded-lg text-on-surface-variant hover:text-error hover:bg-error/10"
                  aria-label="Delete memory"
                >
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
