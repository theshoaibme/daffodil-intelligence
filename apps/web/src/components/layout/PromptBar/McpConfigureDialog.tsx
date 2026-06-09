import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Compass, Loader2, Plus, Trash2, X } from "lucide-react";
import {
  addLocalMcpServer,
  removeLocalMcpServer,
  type LocalMcpServer,
} from "@lib";
import type { McpStatus } from "@hooks";
import { dropdownPanelVariants } from "@lib";
import { FIELD_CLASS } from "@lib";

interface McpConfigureDialogProps {
  open: boolean;
  onClose: () => void;
  status: McpStatus;
  localServers: LocalMcpServer[];
  onLocalServersChange: (servers: LocalMcpServer[]) => void;
  loading?: boolean;
}

const inputClass = FIELD_CLASS;

export function McpConfigureDialog({
  open,
  onClose,
  status,
  localServers,
  onLocalServersChange,
  loading = false,
}: McpConfigureDialogProps) {
  const [name, setName] = useState("");
  const [command, setCommand] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleAdd = () => {
    setError(null);
    if (!name.trim() || !command.trim()) {
      setError("Server name and command are required.");
      return;
    }
    const servers = addLocalMcpServer(name, command);
    onLocalServersChange(servers);
    setName("");
    setCommand("");
  };

  const handleRemove = (id: string) => {
    onLocalServersChange(removeLocalMcpServer(id));
  };

  const serverReady = status.configured || localServers.length > 0;

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
        >
          <motion.div
            variants={dropdownPanelVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            style={{ transformOrigin: "center center" }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg rounded-2xl border border-outline-variant/40 bg-surface-container-lowest shadow-xl text-on-surface overflow-hidden"
          >
            <div className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Compass size={18} className="text-primary" />
                </div>
                <div>
                  <h3 className="text-base font-semibold">Configure MCP</h3>
                  <p className="text-xs text-on-surface-variant mt-0.5">
                    Model Context Protocol tools for your agent
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-full hover:bg-surface-container-high text-on-surface-variant border-0 cursor-pointer"
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>

            <div className="px-5 pb-5 space-y-4 max-h-[70vh] overflow-y-auto custom-scrollbar">
              <div
                className={`rounded-xl px-4 py-3 text-sm ${
                  serverReady
                    ? "bg-primary/10 text-primary"
                    : "bg-error/10 text-error"
                }`}
              >
                {loading ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" />
                    Checking MCP status…
                  </span>
                ) : serverReady ? (
                  "MCP is configured and ready to use."
                ) : status.enabled ? (
                  "MCP is enabled but no servers are configured yet."
                ) : (
                  "MCP is disabled on the server. Add local servers below or enable MCP in the API environment."
                )}
              </div>

              {status.servers.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-on-surface-variant mb-2">API servers</p>
                  <ul className="space-y-1.5">
                    {status.servers.map((server) => (
                      <li
                        key={server}
                        className="text-sm px-3 py-2 rounded-lg bg-surface-container-high/60 text-on-surface"
                      >
                        {server}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <p className="text-xs font-medium text-on-surface-variant mb-2">Your MCP servers</p>
                {localServers.length === 0 ? (
                  <p className="text-sm text-on-surface-variant/80">No local servers added yet.</p>
                ) : (
                  <ul className="space-y-1.5">
                    {localServers.map((server) => (
                      <li
                        key={server.id}
                        className="flex items-center justify-between gap-3 px-3 py-2 rounded-lg bg-surface-container-high/60"
                      >
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-on-surface truncate">{server.name}</p>
                          <p className="text-xs text-on-surface-variant truncate">{server.command}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemove(server.id)}
                          className="p-1.5 rounded-lg hover:bg-error/10 text-on-surface-variant hover:text-error border-0 cursor-pointer flex-shrink-0"
                          aria-label={`Remove ${server.name}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="rounded-xl border border-outline-variant/40 p-4 space-y-3">
                <p className="text-sm font-medium text-on-surface">Add MCP server</p>
                <div>
                  <label className="block text-xs font-medium text-on-surface-variant mb-1.5">
                    Server name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={inputClass}
                    placeholder="e.g. filesystem"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-on-surface-variant mb-1.5">
                    Command
                  </label>
                  <input
                    type="text"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                    className={inputClass}
                    placeholder="npx -y @modelcontextprotocol/server-filesystem /tmp"
                  />
                </div>
                {error && (
                  <p className="text-sm text-error" role="alert">
                    {error}
                  </p>
                )}
                <button
                  type="button"
                  onClick={handleAdd}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 border-0 cursor-pointer"
                >
                  <Plus size={14} />
                  Add server
                </button>
              </div>

              <p className="text-xs text-on-surface-variant/70 leading-relaxed">
                Admins can also set <code className="text-on-surface">MCP_EXTERNAL_SERVERS</code> in
                the API <code className="text-on-surface">.env</code> file for production use.
              </p>
            </div>

            <div className="px-5 py-4 flex justify-end border-t border-outline-variant/20">
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2.5 rounded-full bg-surface-container-highest hover:bg-surface-container-high text-sm font-semibold text-on-surface border-0 cursor-pointer"
              >
                Done
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
