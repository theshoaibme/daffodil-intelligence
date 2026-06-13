import { Link } from "react-router-dom";
import { Award, ExternalLink } from "lucide-react";
import { useResearchPaperPath } from "../hooks/useResearchPaperPath";
import { ResearchPaper } from "./types";

interface ResearchPaperCardProps {
  paper: ResearchPaper;
  view?: "grid" | "list";
}

export function ResearchPaperCard({ paper, view = "grid" }: ResearchPaperCardProps) {
  const paperPath = useResearchPaperPath(paper.id);

  if (view === "list") {
    return (
      <div className="flex items-center gap-5 px-5 py-4 bg-surface-container-low rounded-2xl transition-all duration-200 hover:bg-surface-container hover:shadow-md">
        {/* Left: Year + Source */}
        <div className="shrink-0 w-16 text-center space-y-0.5">
          <p className="text-sm font-semibold text-on-surface">{paper.year}</p>
          <p className="text-[10px] text-on-surface-variant/60 truncate">{paper.source}</p>
        </div>

        {/* Divider */}
        <div className="w-px h-10 bg-outline-variant/15 shrink-0" />

        {/* Center: Title + Authors + Abstract */}
        <div className="flex-1 min-w-0 space-y-1 overflow-hidden">
          <div className="flex items-center gap-2 min-w-0">
            <Link
              to={paperPath}
              className="flex-1 min-w-0 font-semibold text-sm text-on-surface line-clamp-1 leading-snug hover:text-primary transition-colors break-words"
            >
              {paper.title}
            </Link>
            <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
              {paper.category}
            </span>
          </div>
          <p className="text-xs text-on-surface-variant/70 truncate">
            {paper.authors}
          </p>
          <p className="text-xs text-on-surface-variant/50 leading-relaxed line-clamp-1 break-words">
            {paper.abstract}
          </p>
        </div>

        {/* Right: Citations + Link */}
        <div className="shrink-0 flex items-center gap-4">
          <div className="flex items-center gap-1 text-on-surface-variant/60">
            <Award size={13} className="text-primary/70" />
            <span className="text-xs font-medium">{paper.citations.toLocaleString()}</span>
          </div>
          <Link
            to={paperPath}
            className="text-xs font-semibold text-primary hover:underline flex items-center gap-0.5"
          >
            View Paper <ExternalLink size={11} />
          </Link>
        </div>
      </div>
    );
  }

  // Grid view (default)
  return (
    <div className="p-5 flex h-[270px] flex-col overflow-hidden bg-surface-container-low rounded-2xl transition-all duration-200 hover:bg-surface-container hover:shadow-md">
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden min-w-0">
        <div className="flex shrink-0 justify-between items-start gap-2">
          <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-full truncate max-w-[70%]">
            {paper.category}
          </span>
          <span className="text-[11px] font-medium text-on-surface-variant/70 shrink-0">{paper.year}</span>
        </div>

        <Link
          to={paperPath}
          className="shrink-0 font-semibold text-base text-on-surface line-clamp-2 leading-snug hover:text-primary transition-colors block break-words"
        >
          {paper.title}
        </Link>

        <p className="shrink-0 text-xs text-on-surface-variant/80 italic truncate">
          By {paper.authors} • {paper.source}
        </p>

        <p className="min-h-0 flex-1 text-xs text-on-surface-variant leading-relaxed line-clamp-3 break-words overflow-hidden">
          {paper.abstract}
        </p>
      </div>

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-outline-variant/10 shrink-0">
        <span className="text-[11px] text-on-surface-variant/60 flex items-center gap-1">
          <Award size={13} className="text-primary/70" />
          {paper.citations.toLocaleString()} citations
        </span>
        <Link
          to={paperPath}
          className="text-[11px] font-semibold text-primary hover:underline flex items-center gap-0.5"
        >
          View Paper <ExternalLink size={11} />
        </Link>
      </div>
    </div>
  );
}
