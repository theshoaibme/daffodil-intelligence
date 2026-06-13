import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  CheckCircle2,
  Compass,
  Loader2,
  Play,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import {
  addLocalMcpServer,
  formatMcpCommand,
  hasLocalMcpServerName,
  removeLocalMcpServer,
  type LocalMcpServer,
  type McpServerTestResult,
} from "@lib";
import type { McpStatus } from "@hooks";
import type { McpStatusDetail } from "@lib";
import { dropdownPanelVariants } from "@lib";
import { FIELD_CLASS, FIELD_LABEL_CLASS } from "@lib";
import { Button } from "@ui";

interface McpConfigureDialogProps {
  open: boolean;
  onClose: () => void;
  status: McpStatus;
  detail: McpStatusDetail | null;
  localServers: LocalMcpServer[];
  onLocalServersChange: (servers: LocalMcpServer[]) => void;
  loading?: boolean;
  syncing?: boolean;
  onRefreshStatus?: () => void;
  onValidateServer?: (name: string, command: string) => Promise<{ valid: boolean; errors: string[] }>;
  onTestServer?: (name: string, command: string) => Promise<McpServerTestResult>;
  onTestSelf?: () => Promise<McpServerTestResult>;
}

type ListedServer =
  | {
      key: string;
      name: string;
      command: string;
      source: "env" | "local";
      removable: false;
    }
  | {
      key: string;
      id: string;
      name: string;
      command: string;
      source: "local";
      removable: true;
    };

type TestState = {
  loading: boolean;
  result?: McpServerTestResult;
  error?: string;
};

function StatusDot({ ready, loading }: { ready: boolean; loading: boolean }) {
  if (loading) {
    return <Loader2 size={12} className="animate-spin text-on-surface-variant" aria-hidden />;
  }
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${ready ? "bg-primary" : "bg-on-surface-variant/40"}`}
      aria-hidden
    />
  );
}

function statusMessage(status: McpStatus, detail: McpStatusDetail | null): string {
  if (!status.enabled) return "MCP is disabled on the server.";
  if (!status.sdk_available) return "MCP SDK is not installed on the API server.";
  if (detail && !detail.antigravity_available) {
    return "Agent runtime cannot load MCP servers yet.";
  }
  if (status.status === "configured") return "Server MCP integration is active.";
  if (status.status === "needs_configuration") return "Add at least one MCP server to use tools.";
  return "Checking MCP status…";
}

function TestResultBadge({ result }: { result: McpServerTestResult }) {
  if (result.success) {
    return (
      <p className="text-xs text-primary mt-1">
        Connected · {result.tool_count} tool{result.tool_count === 1 ? "" : "s"}
        {result.latency_ms ? ` · ${Math.round(result.latency_ms)}ms` : ""}
      </p>
    );
  }
  return (
    <p className="text-xs text-error mt-1" role="alert">
      {result.error || result.message}
    </p>
  );
}

export function McpConfigureDialog({
  open,
  onClose,
  status,
  detail,
  localServers,
  onLocalServersChange,
  loading = false,
  syncing = false,
  onRefreshStatus,
  onValidateServer,
  onTestServer,
  onTestSelf,
}: McpConfigureDialogProps) {
  const [name, setName] = useState("");
  const [command, setCommand] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [testStates, setTestStates] = useState<Record<string, TestState>>({});
  const [selfTest, setSelfTest] = useState<TestState>({ loading: false });

  const serverReady = status.configured || localServers.length > 0;

  const listedServers = useMemo<ListedServer[]>(() => {
    const envServers: ListedServer[] = (detail?.servers ?? []).map((server) => ({
      key: `env-${server.name}`,
      name: server.name,
      command: formatMcpCommand(server),
      source: "env" as const,
      removable: false as const,
    }));
    const browserServers: ListedServer[] = localServers.map((server) => ({
      key: server.id,
      id: server.id,
      name: server.name,
      command: server.command,
      source: "local" as const,
      removable: true as const,
    }));
    const envNames = new Set(envServers.map((server) => server.name.toLowerCase()));
    return [
      ...envServers,
      ...browserServers.filter((server) => !envNames.has(server.name.toLowerCase())),
    ];
  }, [detail?.servers, localServers]);

  const statusLabel = loading
    ? "Checking…"
    : serverReady
      ? `${listedServers.length} server${listedServers.length === 1 ? "" : "s"}`
      : status.enabled
        ? "Add a server"
        : "Unavailable";

  useEffect(() => {
    if (!open) {
      setName("");
      setCommand("");
      setError(null);
      setAdding(false);
      setTestStates({});
      setSelfTest({ loading: false });
      return;
    }

    onRefreshStatus?.();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose, onRefreshStatus]);

  const setTestState = (key: string, next: TestState) => {
    setTestStates((prev) => ({ ...prev, [key]: next }));
  };

  const handleTest = async (server: ListedServer) => {
    if (!onTestServer) return;
    setTestState(server.key, { loading: true });
    try {
      const result = await onTestServer(server.name, server.command);
      setTestState(server.key, { loading: false, result });
    } catch (err) {
      setTestState(server.key, {
        loading: false,
        error: err instanceof Error ? err.message : "Test failed",
      });
    }
  };

  const handleTestSelf = async () => {
    if (!onTestSelf) return;
    setSelfTest({ loading: true });
    try {
      const result = await onTestSelf();
      setSelfTest({ loading: false, result });
    } catch (err) {
      setSelfTest({
        loading: false,
        error: err instanceof Error ? err.message : "Test failed",
      });
    }
  };

  const handleAdd = async () => {
    setError(null);
    const trimmedName = name.trim();
    const trimmedCommand = command.trim();

    if (!trimmedName || !trimmedCommand) {
      setError("Name and command are required.");
      return;
    }
    if (hasLocalMcpServerName(trimmedName)) {
      setError("A server with this name already exists.");
      return;
    }
    if (
      (detail?.servers ?? []).some(
        (server) => server.name.toLowerCase() === trimmedName.toLowerCase()
      )
    ) {
      setError("This name is already used by a server configured on the API.");
      return;
    }

    setAdding(true);
    try {
      if (onValidateServer) {
        const validation = await onValidateServer(trimmedName, trimmedCommand);
        if (!validation.valid) {
          setError(validation.errors.join(" ") || "Invalid server configuration.");
          return;
        }
      }

      const servers = addLocalMcpServer(trimmedName, trimmedCommand);
      onLocalServersChange(servers);
      setName("");
      setCommand("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add server.");
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = (id: string) => {
    onLocalServersChange(removeLocalMcpServer(id));
    setTestStates((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void handleAdd();
  };

  const canUseMcp = status.enabled && status.sdk_available;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/70 backdrop-blur-sm"
          onClick={onClose}
          role="presentation"
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="mcp-dialog-title"
            variants={dropdownPanelVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            style={{ transformOrigin: "center center" }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border border-outline-variant/40 bg-surface-container-lowest shadow-xl text-on-surface overflow-hidden"
          >
            <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-outline-variant/20">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <Compass size={16} className="text-primary" />
                </div>
                <div className="min-w-0">
                  <h3 id="mcp-dialog-title" className="text-sm font-semibold">
                    MCP servers
                  </h3>
                  <p className="flex items-center gap-1.5 text-xs text-on-surface-variant mt-0.5">
                    <StatusDot ready={serverReady} loading={loading || syncing} />
                    <span>{syncing ? "Saving…" : statusLabel}</span>
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-full hover:bg-surface-container-high text-on-surface-variant border-0 cursor-pointer"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            <div className="px-5 py-4 space-y-4 max-h-[65vh] overflow-y-auto custom-scrollbar">
              <div
                className={`rounded-xl px-3 py-2.5 text-xs ${
                  canUseMcp
                    ? "bg-surface-container-high/50 text-on-surface-variant"
                    : "bg-error/10 text-error"
                }`}
              >
                <p>{statusMessage(status, detail)}</p>
                {detail && detail.local_tool_count > 0 && (
                  <p className="mt-1 text-on-surface-variant/80">
                    Built-in Daffodil tools: {detail.local_tool_count}
                  </p>
                )}
              </div>

              {detail && canUseMcp && onTestSelf && (
                <div className="flex items-center justify-between gap-3 rounded-xl bg-surface-container-high/40 px-3 py-2.5">
                  <div className="min-w-0">
                    <p className="text-sm font-medium">Daffodil MCP server</p>
                    <p className="text-xs text-on-surface-variant truncate">
                      Built-in tool server for this project
                    </p>
                    {selfTest.result && <TestResultBadge result={selfTest.result} />}
                    {selfTest.error && (
                      <p className="text-xs text-error mt-1" role="alert">
                        {selfTest.error}
                      </p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => void handleTestSelf()}
                    disabled={selfTest.loading}
                    className="shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-surface-container-high hover:bg-surface-container-highest border-0 cursor-pointer disabled:opacity-50"
                  >
                    {selfTest.loading ? (
                      <Loader2 size={13} className="animate-spin" />
                    ) : (
                      <Play size={13} />
                    )}
                    Test
                  </button>
                </div>
              )}

              {listedServers.length > 0 ? (
                <ul className="space-y-2">
                  {listedServers.map((server) => {
                    const testState = testStates[server.key];
                    return (
                      <li
                        key={server.key}
                        className="px-3 py-2.5 rounded-xl bg-surface-container-high/50"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 min-w-0">
                              <p className="text-sm font-medium text-on-surface truncate">
                                {server.name}
                              </p>
                              <span className="shrink-0 text-[10px] uppercase tracking-wide text-on-surface-variant/70">
                                {server.source}
                              </span>
                            </div>
                            <p className="text-xs text-on-surface-variant break-all mt-0.5">
                              {server.command}
                            </p>
                            {testState?.result && <TestResultBadge result={testState.result} />}
                            {testState?.error && (
                              <p className="text-xs text-error mt-1" role="alert">
                                {testState.error}
                              </p>
                            )}
                            {testState?.result?.success && testState.result.tools.length > 0 && (
                              <p className="text-[11px] text-on-surface-variant/80 mt-1 line-clamp-2">
                                {testState.result.tools.slice(0, 6).join(", ")}
                                {testState.result.tools.length > 6 ? "…" : ""}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-1 shrink-0">
                            {onTestServer && canUseMcp && (
                              <button
                                type="button"
                                onClick={() => void handleTest(server)}
                                disabled={testState?.loading}
                                title="Test connection"
                                aria-label={`Test ${server.name}`}
                                className="p-1.5 rounded-lg hover:bg-surface-container-highest text-on-surface-variant border-0 cursor-pointer disabled:opacity-50"
                              >
                                {testState?.loading ? (
                                  <Loader2 size={14} className="animate-spin" />
                                ) : testState?.result?.success ? (
                                  <CheckCircle2 size={14} className="text-primary" />
                                ) : (
                                  <Play size={14} />
                                )}
                              </button>
                            )}
                            {server.removable && (
                              <button
                                type="button"
                                onClick={() => handleRemove(server.id)}
                                className="p-1.5 rounded-lg hover:bg-error/10 text-on-surface-variant hover:text-error border-0 cursor-pointer"
                                aria-label={`Remove ${server.name}`}
                              >
                                <Trash2 size={14} />
                              </button>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="text-sm text-on-surface-variant/80 py-1">No servers configured yet.</p>
              )}

              <form onSubmit={handleSubmit} className="space-y-3 pt-1 border-t border-outline-variant/15">
                <p className="text-xs font-medium text-on-surface-variant pt-2">Add MCP server</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="mcp-server-name" className={FIELD_LABEL_CLASS}>
                      Name
                    </label>
                    <input
                      id="mcp-server-name"
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className={FIELD_CLASS}
                      placeholder="filesystem"
                      autoComplete="off"
                      disabled={!canUseMcp || adding}
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label htmlFor="mcp-server-command" className={FIELD_LABEL_CLASS}>
                      Command
                    </label>
                    <input
                      id="mcp-server-command"
                      type="text"
                      value={command}
                      onChange={(e) => setCommand(e.target.value)}
                      className={FIELD_CLASS}
                      placeholder="npx -y @modelcontextprotocol/server-filesystem /tmp"
                      autoComplete="off"
                      disabled={!canUseMcp || adding}
                    />
                    <p className="text-[11px] text-on-surface-variant/70 mt-1">
                      Full shell command. The API validates and probes stdio servers before saving.
                    </p>
                  </div>
                </div>

                {error && (
                  <p className="flex items-start gap-1.5 text-xs text-error" role="alert">
                    <AlertCircle size={14} className="shrink-0 mt-0.5" />
                    <span>{error}</span>
                  </p>
                )}

                <Button
                  type="submit"
                  size="sm"
                  variant="tonal"
                  className="gap-1.5"
                  disabled={!canUseMcp || adding || !name.trim() || !command.trim()}
                >
                  {adding ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
                  {adding ? "Adding…" : "Add server"}
                </Button>
              </form>
            </div>

            <div className="px-5 py-3 flex justify-end border-t border-outline-variant/20">
              <Button type="button" size="sm" variant="text" onClick={onClose}>
                Done
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
