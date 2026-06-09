import { useEffect, useMemo, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Compass, Loader2, Plus, Trash2, X } from "lucide-react";
import {
  addLocalMcpServer,
  hasLocalMcpServerName,
  removeLocalMcpServer,
  type LocalMcpServer,
} from "@lib";
import type { McpStatus } from "@hooks";
import { dropdownPanelVariants } from "@lib";
import { FIELD_CLASS, FIELD_LABEL_CLASS } from "@lib";
import { Button } from "@ui";

interface McpConfigureDialogProps {
  open: boolean;
  onClose: () => void;
  status: McpStatus;
  localServers: LocalMcpServer[];
  onLocalServersChange: (servers: LocalMcpServer[]) => void;
  loading?: boolean;
  onRefreshStatus?: () => void;
}

type ListedServer =
  | { key: string; name: string; command?: string; source: "api"; removable: false }
  | { key: string; name: string; command: string; source: "local"; removable: true; id: string };

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

export function McpConfigureDialog({
  open,
  onClose,
  status,
  localServers,
  onLocalServersChange,
  loading = false,
  onRefreshStatus,
}: McpConfigureDialogProps) {
  const [name, setName] = useState("");
  const [command, setCommand] = useState("");
  const [error, setError] = useState<string | null>(null);

  const serverReady = status.configured || localServers.length > 0;

  const listedServers = useMemo<ListedServer[]>(() => {
    const apiServers: ListedServer[] = status.servers.map((server) => ({
      key: `api-${server}`,
      name: server,
      source: "api",
      removable: false,
    }));
    const browserServers: ListedServer[] = localServers.map((server) => ({
      key: server.id,
      id: server.id,
      name: server.name,
      command: server.command,
      source: "local",
      removable: true,
    }));
    return [...apiServers, ...browserServers];
  }, [localServers, status.servers]);

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

  const handleAdd = () => {
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
    if (status.servers.some((server) => server.toLowerCase() === trimmedName.toLowerCase())) {
      setError("This name is already used by an API server.");
      return;
    }

    const servers = addLocalMcpServer(trimmedName, trimmedCommand);
    onLocalServersChange(servers);
    setName("");
    setCommand("");
  };

  const handleRemove = (id: string) => {
    onLocalServersChange(removeLocalMcpServer(id));
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    handleAdd();
  };

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
            className="w-full max-w-md rounded-2xl border border-outline-variant/40 bg-surface-container-lowest shadow-xl text-on-surface overflow-hidden"
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
                    <StatusDot ready={serverReady} loading={loading} />
                    <span>{statusLabel}</span>
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

            <div className="px-5 py-4 space-y-4 max-h-[60vh] overflow-y-auto custom-scrollbar">
              {listedServers.length > 0 ? (
                <ul className="space-y-2">
                  {listedServers.map((server) => (
                    <li
                      key={server.key}
                      className="flex items-start justify-between gap-3 px-3 py-2.5 rounded-xl bg-surface-container-high/50"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 min-w-0">
                          <p className="text-sm font-medium text-on-surface truncate">{server.name}</p>
                          <span className="shrink-0 text-[10px] uppercase tracking-wide text-on-surface-variant/70">
                            {server.source}
                          </span>
                        </div>
                        {server.command && (
                          <p className="text-xs text-on-surface-variant truncate mt-0.5">{server.command}</p>
                        )}
                      </div>
                      {server.removable && (
                        <button
                          type="button"
                          onClick={() => handleRemove(server.id)}
                          className="p-1.5 rounded-lg hover:bg-error/10 text-on-surface-variant hover:text-error border-0 cursor-pointer shrink-0"
                          aria-label={`Remove ${server.name}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-on-surface-variant/80 py-2">No servers yet.</p>
              )}

              <form onSubmit={handleSubmit} className="space-y-3 pt-1">
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
                    />
                  </div>
                </div>

                {error && (
                  <p className="text-xs text-error" role="alert">
                    {error}
                  </p>
                )}

                <Button
                  type="submit"
                  size="sm"
                  variant="tonal"
                  className="gap-1.5"
                  disabled={!name.trim() || !command.trim()}
                >
                  <Plus size={14} />
                  Add
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
