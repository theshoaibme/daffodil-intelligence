interface ResearchDropdownProps {
  topSearches: string[];
  recentResearchSearches: string[];
  onSelectSearch: (term: string) => void;
}

export function ResearchDropdown({ topSearches, recentResearchSearches, onSelectSearch }: ResearchDropdownProps) {
  return (
    <div 
      className="absolute left-0 right-0 top-full mt-2 z-50 rounded-3xl shadow-2xl p-5 space-y-4 text-left border border-outline-variant/20"
      style={{ backgroundColor: "var(--color-surface-container-lowest, #ffffff)", opacity: 1 }}
    >
      
      {/* Top Searches Section */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-primary uppercase tracking-wider">Top Searches</h4>
        <div className="flex flex-wrap gap-2">
          {topSearches.map((term) => (
            <button
              key={term}
              type="button"
              onClick={() => onSelectSearch(term)}
              className="px-3.5 py-1.5 rounded-full text-xs font-medium bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high/80 transition-colors border-0 cursor-pointer"
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
        <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1">Research Searches</h4>
        {recentResearchSearches.map((term) => (
          <button
            key={term}
            type="button"
            onClick={() => onSelectSearch(term)}
            className="w-full text-left px-3 py-2 rounded-xl text-xs sm:text-sm text-on-surface hover:bg-surface-container-low transition-colors block truncate border-0 cursor-pointer"
          >
            {term}
          </button>
        ))}
      </div>

    </div>
  );
}
