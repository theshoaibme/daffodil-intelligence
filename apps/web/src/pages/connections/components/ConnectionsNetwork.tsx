import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Building2,
  GraduationCap,
  MessageSquare,
  Search,
  UserPlus,
  Users,
} from "lucide-react";
import { Loader } from "@ui";
import { ROUTES } from "@lib";
import { useAuth } from "@context";
import { useConnectionsNetwork } from "../hooks/useConnectionsNetwork";
import type { ConnectionKind, ResearchConnection } from "../types";
import { ConnectionCard } from "./ConnectionCard";
import { ConnectionMessageDialog } from "./ConnectionMessageDialog";
import { ResearchPagination } from "../../research/components/ResearchPagination";

type FilterType = "all" | ConnectionKind | "connected";
const ITEMS_PER_PAGE = 9;

interface ConnectionsNetworkProps {
  workspace?: boolean;
}

export function ConnectionsNetwork({ workspace = false }: ConnectionsNetworkProps) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const {
    connections,
    stats,
    loading,
    error,
    refresh,
    getStatus,
    connect,
    acceptConnection,
    sendMessage,
    loadMessages,
    getMessages,
    connectedCount,
  } = useConnectionsNetwork(isAuthenticated);

  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [activeMessage, setActiveMessage] = useState<ResearchConnection | null>(null);

  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return connections.filter((item) => {
      const status = getStatus(item.id);
      const matchesFilter =
        filter === "all" ||
        (filter === "connected" ? status === "connected" : item.kind === filter);
      const matchesSearch =
        !q ||
        item.name.toLowerCase().includes(q) ||
        item.subtitle.toLowerCase().includes(q) ||
        item.focus.toLowerCase().includes(q) ||
        (item.featuredPaper?.title.toLowerCase().includes(q) ?? false);
      return matchesFilter && matchesSearch;
    });
  }, [connections, searchQuery, filter, getStatus]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const currentItems = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filtered.slice(start, start + ITEMS_PER_PAGE);
  }, [filtered, currentPage]);

  const requireAuth = (action: () => void) => {
    if (!workspace || isAuthenticated) {
      action();
      return;
    }
    navigate(ROUTES.login);
  };

  const handleConnect = (item: ResearchConnection) => {
    requireAuth(() => {
      const status = getStatus(item.id);
      if (status === "pending") {
        void acceptConnection(item.id);
      } else if (status === "available") {
        void connect(item.id);
      }
    });
  };

  const handleMessage = (item: ResearchConnection) => {
    if (!isAuthenticated) {
      navigate(ROUTES.login);
      return;
    }
    requireAuth(() => {
      void loadMessages(item.id);
      setActiveMessage(item);
    });
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="space-y-2">
        <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-on-surface">
          Research connections
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-on-surface-variant">
          Discover researchers and institutions from your paper library. Connect, send formal
          correspondence, and collaborate around shared publications.
        </p>
        {!workspace && !isAuthenticated && (
          <p className="text-sm text-on-surface-variant">
            <Link to={ROUTES.register} className="font-semibold text-primary hover:underline">
              Create an account
            </Link>{" "}
            or{" "}
            <Link to={ROUTES.login} className="font-semibold text-primary hover:underline">
              sign in
            </Link>{" "}
            to connect and send formal correspondence.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Researchers", value: stats.researchers, icon: GraduationCap },
          { label: "Institutions", value: stats.institutions, icon: Building2 },
          { label: "Your connections", value: isAuthenticated ? connectedCount : "—", icon: Users },
        ].map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="flex items-center gap-3 rounded-2xl bg-surface-container-low px-5 py-4"
          >
            <div className="rounded-xl bg-primary/10 p-2 text-primary">
              <Icon size={18} />
            </div>
            <div>
              <p className="text-xs text-on-surface-variant">{label}</p>
              <p className="text-xl font-semibold tabular-nums text-on-surface">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-lg font-semibold text-on-surface">Network ({filtered.length})</h3>
          <div className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row sm:items-center">
            <div className="flex flex-wrap gap-1.5">
              {(
                [
                  { id: "all", label: "All" },
                  { id: "researcher", label: "Researchers" },
                  { id: "institution", label: "Institutions" },
                  { id: "connected", label: "Connected" },
                ] as const
              ).map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    setFilter(id);
                    setCurrentPage(1);
                  }}
                  className={`cursor-pointer rounded-full border-0 px-3 py-1.5 text-xs font-semibold transition-all ${
                    filter === id
                      ? "bg-primary text-on-primary"
                      : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="relative w-full sm:max-w-xs">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60"
              />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search by name, paper, or field..."
                className="w-full rounded-xl border-0 bg-surface-container-lowest py-2.5 pl-9 pr-4 text-sm text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center rounded-3xl bg-surface-container-low/50 p-12">
            <Loader variant="spinner" diameter={36} strokeWidth={3} color="primary" message="Loading network..." />
          </div>
        ) : error ? (
          <div className="space-y-3 rounded-3xl bg-surface-container-low/50 p-10 text-center text-on-surface-variant">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => refresh()}
              className="cursor-pointer border-0 bg-transparent text-sm font-semibold text-primary hover:underline"
            >
              Retry
            </button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="rounded-3xl bg-surface-container-low/50 p-10 text-center text-on-surface-variant">
            No connections match your search.
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
              {currentItems.map((item) => (
                <ConnectionCard
                  key={item.id}
                  item={item}
                  status={isAuthenticated ? getStatus(item.id) : "available"}
                  workspace={workspace}
                  onConnect={() => handleConnect(item)}
                  onMessage={() => handleMessage(item)}
                />
              ))}
            </div>
            {filtered.length > ITEMS_PER_PAGE && (
              <div className="flex justify-center border-t border-outline-variant/10 pt-4">
                <ResearchPagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                />
              </div>
            )}
          </>
        )}
      </div>

      {!workspace && (
        <div className="rounded-2xl bg-surface-container-low px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-start gap-3">
            <MessageSquare size={18} className="text-primary shrink-0 mt-0.5" />
            <p className="text-sm text-on-surface-variant">
              Manage integrations like MCP servers from your{" "}
              <Link to={ROUTES.home} className="font-semibold text-primary hover:underline">
                studio workspace
              </Link>
              .
            </p>
          </div>
          <Link
            to={ROUTES.connections}
            className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-on-primary hover:opacity-90"
          >
            <UserPlus size={14} />
            Open studio connections
          </Link>
        </div>
      )}

      {activeMessage && (
        <ConnectionMessageDialog
          connection={activeMessage}
          messages={getMessages(activeMessage.id)}
          onClose={() => setActiveMessage(null)}
          onSend={(payload) => {
            void sendMessage(activeMessage.id, payload);
          }}
        />
      )}
    </div>
  );
}
