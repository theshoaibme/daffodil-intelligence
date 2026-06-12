import { Award, ExternalLink } from "lucide-react";
import { ResearchPaper } from "./types";

interface ResearchPaperCardProps {
  paper: ResearchPaper;
  view?: "grid" | "list";
}

export function ResearchPaperCard({ paper, view = "grid" }: ResearchPaperCardProps) {
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
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-sm text-on-surface line-clamp-1 leading-snug hover:text-primary transition-colors">
              {paper.title}
            </h4>
            <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full whitespace-nowrap shrink-0">
              {paper.category}
            </span>
          </div>
          <p className="text-xs text-on-surface-variant/70 truncate">
            {paper.authors}
          </p>
          <p className="text-xs text-on-surface-variant/50 leading-relaxed line-clamp-1">{paper.abstract}</p>
        </div>

        {/* Right: Citations + Link */}
        <div className="shrink-0 flex items-center gap-4">
          <div className="flex items-center gap-1 text-on-surface-variant/60">
            <Award size={13} className="text-primary/70" />
            <span className="text-xs font-medium">{paper.citations.toLocaleString()}</span>
          </div>
          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-semibold text-primary hover:underline flex items-center gap-0.5"
            >
              View <ExternalLink size={11} />
            </a>
          )}
        </div>
      </div>
    );
  }

  // Grid view (default)
  return (
    <div className="p-5 flex flex-col justify-between bg-surface-container-low rounded-2xl transition-all duration-200 hover:bg-surface-container hover:shadow-md h-[270px]">
      <div className="space-y-2 min-w-0">
        <div className="flex justify-between items-start gap-2">
          <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-full">
            {paper.category}
          </span>
          <span className="text-[11px] font-medium text-on-surface-variant/70">{paper.year}</span>
        </div>

        <h4 className="font-semibold text-base text-on-surface line-clamp-2 leading-snug hover:text-primary transition-colors">
          {paper.title}
        </h4>

        <p className="text-xs text-on-surface-variant/80 italic truncate">
          By {paper.authors} • {paper.source}
        </p>

        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-3">{paper.abstract}</p>
      </div>

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-outline-variant/10 shrink-0">
        <span className="text-[11px] text-on-surface-variant/60 flex items-center gap-1">
          <Award size={13} className="text-primary/70" />
          {paper.citations.toLocaleString()} citations
        </span>
        {paper.url && (
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] font-semibold text-primary hover:underline flex items-center gap-0.5"
          >
            View Paper <ExternalLink size={11} />
          </a>
        )}
      </div>
    </div>
  );
}
