import { Link } from "react-router-dom";
import { Award, Eye, Pencil, Trash2 } from "lucide-react";
import { researchPaperPath } from "@lib";
import { ResearchPaper } from "./types";

interface ResearchPaperManageCardProps {
  paper: ResearchPaper;
  view: "grid" | "list";
  onEdit: () => void;
  onDelete: () => void;
}

function ManageActions({
  paperId,
  onEdit,
  onDelete,
  compact = false,
}: {
  paperId: string;
  onEdit: () => void;
  onDelete: () => void;
  compact?: boolean;
}) {
  const btnClass = compact
    ? "p-1.5 rounded-lg"
    : "p-2 rounded-lg";

  return (
    <div className="flex items-center gap-0.5 shrink-0">
      <Link
        to={researchPaperPath(paperId, { workspace: true })}
        className={`${btnClass} text-on-surface-variant hover:text-primary hover:bg-primary/10 transition-colors`}
        title="View paper"
      >
        <Eye size={compact ? 15 : 16} />
      </Link>
      <button
        type="button"
        onClick={onEdit}
        className={`${btnClass} text-on-surface-variant hover:text-primary hover:bg-primary/10 transition-colors cursor-pointer border-0`}
        title="Edit paper"
      >
        <Pencil size={compact ? 15 : 16} />
      </button>
      <button
        type="button"
        onClick={onDelete}
        className={`${btnClass} text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors cursor-pointer border-0`}
        title="Delete paper"
      >
        <Trash2 size={compact ? 15 : 16} />
      </button>
    </div>
  );
}

export function ResearchPaperManageCard({
  paper,
  view,
  onEdit,
  onDelete,
}: ResearchPaperManageCardProps) {
  if (view === "list") {
    return (
      <div className="flex items-center gap-4 sm:gap-5 px-4 sm:px-5 py-4 bg-surface-container-low rounded-2xl transition-all duration-200 hover:bg-surface-container">
        <div className="shrink-0 w-14 sm:w-16 text-center space-y-0.5">
          <p className="text-sm font-semibold text-on-surface">{paper.year}</p>
          <p className="text-[10px] text-on-surface-variant/60 truncate">{paper.source}</p>
        </div>

        <div className="w-px h-10 bg-outline-variant/15 shrink-0" />

        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2 min-w-0">
            <p className="font-semibold text-sm text-on-surface line-clamp-1 leading-snug">
              {paper.title}
            </p>
            <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
              {paper.category}
            </span>
          </div>
          <p className="text-xs text-on-surface-variant/70 truncate">{paper.authors}</p>
          <p className="text-xs text-on-surface-variant/50 leading-relaxed line-clamp-1 hidden sm:block">
            {paper.abstract}
          </p>
        </div>

        <div className="shrink-0 flex items-center gap-3 sm:gap-4">
          <div className="hidden sm:flex items-center gap-1 text-on-surface-variant/60">
            <Award size={13} className="text-primary/70" />
            <span className="text-xs font-medium">{paper.citations.toLocaleString()}</span>
          </div>
          <ManageActions
            paperId={paper.id}
            onEdit={onEdit}
            onDelete={onDelete}
            compact
          />
        </div>
      </div>
    );
  }

  return (
    <div className="p-5 flex flex-col justify-between bg-surface-container-low rounded-2xl transition-all duration-200 hover:bg-surface-container min-h-[240px]">
      <div className="space-y-2 min-w-0">
        <div className="flex justify-between items-start gap-2">
          <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-full">
            {paper.category}
          </span>
          <span className="text-[11px] font-medium text-on-surface-variant/70">{paper.year}</span>
        </div>

        <p className="font-semibold text-base text-on-surface line-clamp-2 leading-snug">
          {paper.title}
        </p>

        <p className="text-xs text-on-surface-variant/80 italic truncate">
          By {paper.authors} • {paper.source}
        </p>

        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-3">
          {paper.abstract}
        </p>
      </div>

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-outline-variant/10 shrink-0">
        <span className="text-[11px] text-on-surface-variant/60 flex items-center gap-1">
          <Award size={13} className="text-primary/70" />
          {paper.citations.toLocaleString()} citations
        </span>
        <ManageActions paperId={paper.id} onEdit={onEdit} onDelete={onDelete} />
      </div>
    </div>
  );
}
