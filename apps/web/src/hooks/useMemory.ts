import { useCallback, useEffect, useState } from "react";
import { memoryApi, MemoryRecord, MemoryStats } from "../lib/memoryApi";

export type MemoryTab = "facts" | "conversations" | "configuration" | "subagents";

const TAB_TYPES: Record<MemoryTab, string[] | undefined> = {
  facts: ["fact", "preference", "episode"],
  conversations: ["conversation_turn", "conversation_summary"],
  configuration: [
    "system_prompt",
    "skill",
    "ruleset",
    "tool_definition",
    "mcp_server",
    "agent_config",
  ],
  subagents: ["subagent_definition", "subagent_result"],
};

export function useMemory(tab: MemoryTab, agentId?: string, searchQuery?: string) {
  const [items, setItems] = useState<MemoryRecord[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const types = TAB_TYPES[tab];
      if (searchQuery?.trim()) {
        const type = types?.length === 1 ? types[0] : undefined;
        const result = await memoryApi.recall(searchQuery.trim(), {
          agent_id: agentId,
          memory_type: type,
          k: 20,
        });
        setItems(result.notes);
      } else if (tab === "configuration" && agentId) {
        const result = await memoryApi.context(agentId);
        setItems(result.snapshots);
      } else {
        const results: MemoryRecord[] = [];
        const typeList = types ?? [undefined];
        for (const t of typeList) {
          const res = await memoryApi.list({
            agent_id: agentId,
            memory_type: t,
            limit: 30,
          });
          results.push(...res.items);
        }
        setItems(results);
      }
      const s = await memoryApi.stats();
      setStats(s);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load memory");
    } finally {
      setLoading(false);
    }
  }, [tab, agentId, searchQuery]);

  useEffect(() => {
    load();
  }, [load]);

  const addMemory = useCallback(
    async (text: string, memoryType = "fact") => {
      await memoryApi.remember({ text, agent_id: agentId || "main", memory_type: memoryType });
      await load();
    },
    [agentId, load]
  );

  const deleteMemory = useCallback(
    async (id: string) => {
      await memoryApi.delete(id);
      await load();
    },
    [load]
  );

  const clearScoped = useCallback(
    async (opts?: { memory_type?: string; all?: boolean }) => {
      await memoryApi.clear({
        agent_id: agentId,
        memory_type: opts?.memory_type,
        all: opts?.all,
      });
      await load();
    },
    [agentId, load]
  );

  const consolidate = useCallback(async () => {
    await memoryApi.consolidate();
    await load();
  }, [load]);

  return {
    items,
    stats,
    loading,
    error,
    reload: load,
    addMemory,
    deleteMemory,
    clearScoped,
    consolidate,
  };
}
