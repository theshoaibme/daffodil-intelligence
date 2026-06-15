import { Link } from "react-router-dom";
import { Award, Building2, FileText, GraduationCap, MessageSquare, UserPlus } from "lucide-react";
import { researchPaperPath } from "@lib";
import type { ConnectionStatus, ResearchConnection } from "../types";

interface ConnectionCardProps {
  item: ResearchConnection;
  status: ConnectionStatus;
  workspace?: boolean;
  onConnect: () => void;
  onMessage: () => void;
}

function statusLabel(status: ConnectionStatus): string {
  if (status === "connected") return "Connected";
  if (status === "pending") return "Pending";
  return "Available";
}

function statusClass(status: ConnectionStatus): string {
  if (status === "connected") return "bg-emerald-500/10 text-emerald-600";
  if (status === "pending") return "bg-amber-500/10 text-amber-700";
  return "bg-surface-container-high text-on-surface-variant";
}

export function ConnectionCard({
  item,
  status,
  workspace = false,
  onConnect,
  onMessage,
}: ConnectionCardProps) {
  const Icon = item.kind === "institution" ? Building2 : GraduationCap;
  const connectLabel = status === "pending" ? "Accept" : status === "connected" ? "Connected" : "Connect";

  return (
    <article className="flex h-[260px] flex-col overflow-hidden rounded-2xl bg-surface-container-low p-5 transition-all duration-200 hover:bg-surface-container">
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden min-w-0">
        <div className="flex shrink-0 items-start justify-between gap-2">
          <span
            className={`max-w-[70%] truncate text-[10px] font-semibold px-2.5 py-1 rounded-full ${
              item.kind === "institution"
                ? "text-primary bg-primary/10"
                : "text-secondary bg-secondary/10"
            }`}
          >
            {item.kind === "institution" ? "Institution" : "Researcher"}
          </span>
          <span className={`shrink-0 text-[10px] font-semibold px-2.5 py-1 rounded-full ${statusClass(status)}`}>
            {statusLabel(status)}
          </span>
        </div>

        <div className="flex shrink-0 items-start gap-3 min-w-0">
          <div className="shrink-0 rounded-xl bg-surface-container-lowest p-2.5">
            <Icon size={18} className="text-primary" />
          </div>
          <div className="min-w-0">
            <h3 className="line-clamp-2 text-base font-semibold leading-snug text-on-surface break-words">
              {item.name}
            </h3>
            <p className="mt-1 truncate text-xs text-on-surface-variant/80">{item.subtitle}</p>
          </div>
        </div>

        <p className="line-clamp-2 shrink-0 text-xs leading-relaxed text-on-surface-variant break-words">
          {item.focus}
        </p>

        {item.featuredPaper && (
          <Link
            to={researchPaperPath(item.featuredPaper.id, { workspace })}
            className="mt-auto line-clamp-1 text-[11px] font-medium text-primary hover:underline"
          >
            <span className="inline-flex items-center gap-1">
              <FileText size={11} />
              {item.featuredPaper.title}
            </span>
          </Link>
        )}
      </div>

      <div className="mt-4 flex shrink-0 items-center justify-between border-t border-outline-variant/10 pt-3">
        <span className="flex items-center gap-2 text-[11px] text-on-surface-variant/70">
          <span className="inline-flex items-center gap-1">
            <FileText size={12} className="text-primary/70" />
            {item.paperCount}
          </span>
          <span className="inline-flex items-center gap-1">
            <Award size={12} className="text-primary/70" />
            {item.citations.toLocaleString()}
          </span>
        </span>
        <div className="flex items-center gap-2">
          {status !== "connected" && (
            <button
              type="button"
              onClick={onConnect}
              className="inline-flex items-center gap-1 rounded-full border-0 bg-transparent px-2 py-1 text-[11px] font-semibold text-primary hover:underline cursor-pointer"
            >
              <UserPlus size={12} />
              {connectLabel}
            </button>
          )}
          <button
            type="button"
            onClick={onMessage}
            disabled={status !== "connected"}
            title={
              status === "connected"
                ? "Open chat"
                : status === "pending"
                  ? "Accept the connection to chat"
                  : "Connect first to start chatting"
            }
            className="inline-flex items-center gap-1 rounded-full border-0 bg-transparent px-2 py-1 text-[11px] font-semibold text-primary hover:underline cursor-pointer disabled:cursor-not-allowed disabled:opacity-40 disabled:no-underline"
          >
            <MessageSquare size={12} />
            {status === "connected" ? "Chat" : "Chat locked"}
          </button>
        </div>
      </div>
    </article>
  );
}
