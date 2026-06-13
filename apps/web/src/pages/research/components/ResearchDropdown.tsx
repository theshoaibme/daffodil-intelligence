import { Award, Search } from "lucide-react";
import { ResearchPaper } from "./types";

interface ResearchDropdownProps {
  topSearches: string[];
  recentResearchSearches: string[];
  onSelectSearch: (term: string) => void;
  onOpenPaper?: (paperId: string) => void;
  searchResults?: ResearchPaper[];
  searchQuery?: string;
}

export function ResearchDropdown({
  topSearches,
  recentResearchSearches,
  onSelectSearch,
  onOpenPaper,
  searchResults = [],
  searchQuery = "",
}: ResearchDropdownProps) {
  const hasQuery = searchQuery.trim().length > 0;
  const results = searchResults.slice(0, 6);

  return (
    <div
      className="absolute left-0 right-0 top-full mt-2 z-50 rounded-3xl shadow-2xl p-5 space-y-3 text-left max-h-[420px] overflow-y-auto"
      style={{ backgroundColor: "var(--color-surface-container-low, #f4f2ff)" }}
    >
      {hasQuery && results.length > 0 ? (
        /* ── Live search results ── */
        <div className="space-y-1.5">
          <h4 className="text-xs font-semibold text-primary flex items-center gap-1.5 mb-2">
            <Search size={12} />
            Results ({searchResults.length})
          </h4>
          {results.map((paper) => (
            <button
              key={paper.id}
              type="button"
              onClick={() => onOpenPaper?.(paper.id) ?? onSelectSearch(paper.title)}
              className="w-full text-left flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-container-high/60 transition-colors border-0 cursor-pointer bg-transparent"
            >
              {/* Year */}
              <span className="shrink-0 text-[11px] font-semibold text-on-surface-variant/60 w-10 text-center">
                {paper.year}
              </span>

              {/* Divider */}
              <div className="w-px h-7 bg-outline-variant/15 shrink-0" />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-on-surface truncate">{paper.title}</p>
                <p className="text-[11px] text-on-surface-variant/60 truncate">
                  {paper.authors} · {paper.source}
                </p>
              </div>

              {/* Category + Citations */}
              <div className="shrink-0 flex items-center gap-2">
                <span className="text-[10px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded-full whitespace-nowrap">
                  {paper.category}
                </span>
                <span className="text-[10px] text-on-surface-variant/50 flex items-center gap-0.5">
                  <Award size={10} />
                  {paper.citations.toLocaleString()}
                </span>
              </div>
            </button>
          ))}
          {searchResults.length > 6 && (
            <p className="text-[11px] text-on-surface-variant/50 text-center pt-1">
              +{searchResults.length - 6} more results below
            </p>
          )}
        </div>
      ) : hasQuery && results.length === 0 ? (
        /* ── No results ── */
        <div className="py-4 text-center text-sm text-on-surface-variant/50">
          No papers found for "{searchQuery}"
        </div>
      ) : (
        /* ── Default: suggestions ── */
        <>
          {/* Top Searches Section */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-primary">Top Searches</h4>
            <div className="flex flex-wrap gap-2">
              {topSearches.map((term) => (
                <button
                  key={term}
                  type="button"
                  onClick={() => onSelectSearch(term)}
                  className="px-3.5 py-1.5 rounded-full text-xs font-medium bg-surface-container text-on-surface-variant hover:bg-surface-container-high/80 transition-colors border-0 cursor-pointer"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>

          {/* Spacer */}
          <div className="h-0.5 bg-outline-variant/10" />

          {/* Recent Research Searches Section */}
          <div className="space-y-1.5">
            <h4 className="text-xs font-semibold text-primary mb-1">Recent Searches</h4>
            {recentResearchSearches.map((term) => (
              <button
                key={term}
                type="button"
                onClick={() => onSelectSearch(term)}
                className="w-full text-left px-3 py-2 rounded-xl text-xs sm:text-sm text-on-surface hover:bg-surface-container-high/60 transition-colors block truncate border-0 cursor-pointer bg-transparent"
              >
                {term}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
