import { useState, useEffect, useRef } from "react";
import { Search, History, FileText } from "lucide-react";

export function ResearchSearch() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const categories = ["All", "Computer Science", "AI & Education", "Smart Grids"];

  const researchSyntheses = [
    {
      topic: "Impact of Large Language Models on Software Engineering Education",
      papers: 14,
      style: "APA 7th Edition",
      status: "Synthesized",
      category: "AI & Education",
      date: "June 12, 2026",
    },
    {
      topic: "Optimization of Campus Shuttle Routing using Deep Reinforcement Learning",
      papers: 8,
      style: "IEEE Style",
      status: "Synthesized",
      category: "Computer Science",
      date: "June 10, 2026",
    },
    {
      topic: "Comparison of Quantum Cryptography Protocols in Smart Grids",
      papers: 22,
      style: "IEEE Style",
      status: "Synthesized",
      category: "Smart Grids",
      date: "June 05, 2026",
    },
  ];

  const topSearches = [
    "Deep Learning in CS",
    "Smart Grids Optimization",
    "Academic Writing Formats",
  ];

  const recentResearchSearches = [
    "Impact of Large Language Models on Software Engineering Education",
    "Optimization of Campus Shuttle Routing using Deep Reinforcement Learning",
    "Comparison of Quantum Cryptography Protocols in Smart Grids",
  ];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredSyntheses = researchSyntheses.filter((item) => {
    const matchesSearch = item.topic.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6 sm:space-y-8 relative overflow-hidden">
      {/* Centered Search & Category Filter Section */}
      <div className="flex flex-col items-center gap-4 text-center relative z-10 max-w-2xl mx-auto">
        <div ref={searchRef} className="relative w-full">
          <div className="relative w-full">
            <Search
              size={20}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/60 pointer-events-none"
            />
            <input
              type="text"
              value={searchQuery}
              onFocus={() => setIsDropdownOpen(true)}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search recent syntheses by topic..."
              className="w-full bg-surface-container-low/85 rounded-full pl-12 pr-6 py-3.5 text-base text-on-surface placeholder:text-on-surface-variant/75 focus:outline-none focus:ring-0 focus:border-transparent outline-none border-0 transition-all"
            />
          </div>

          {/* Dropdown Menu - NO border, only shadow and bg */}
          {isDropdownOpen && (
            <div 
              className="absolute left-0 right-0 top-full mt-2 z-50 rounded-3xl shadow-2xl p-5 space-y-4 text-left"
              style={{ backgroundColor: "var(--color-surface-container, #eeecfa)" }}
            >
              
              {/* Top Searches Section */}
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-primary uppercase tracking-wider">Top Searches</h4>
                <div className="flex flex-wrap gap-2">
                  {topSearches.map((term) => (
                    <button
                      key={term}
                      type="button"
                      onClick={() => {
                        setSearchQuery(term);
                        setIsDropdownOpen(false);
                      }}
                      className="px-3.5 py-1.5 rounded-full text-xs font-medium bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high/80 transition-colors border-0 cursor-pointer"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>

              {/* Space block instead of border divider line */}
              <div className="h-2" />

              {/* Recent Research Searches Section */}
              <div className="space-y-1.5">
                <h4 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1">Research Searches</h4>
                {recentResearchSearches.map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => {
                      setSearchQuery(term);
                      setIsDropdownOpen(false);
                    }}
                    className="w-full text-left px-3 py-2 rounded-xl text-xs sm:text-sm text-on-surface hover:bg-surface-container-high transition-colors block truncate border-0 cursor-pointer"
                  >
                    {term}
                  </button>
                ))}
              </div>

            </div>
          )}
        </div>
        
        <div className="flex flex-wrap justify-center gap-2 mt-1">
          {categories.map((cat) => {
            const isActive = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-5 py-2 rounded-full text-xs sm:text-sm font-semibold tracking-wide transition-all duration-200 cursor-pointer ${
                  isActive 
                    ? "bg-primary text-on-primary shadow-sm scale-105" 
                    : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Filtered Results List */}
      <div className="space-y-4 relative z-10 text-left">
        <h3 className="text-lg sm:text-xl font-semibold text-on-surface flex items-center gap-2 mb-2">
          <History className="text-primary" size={20} />
          Recent Syntheses
        </h3>
        
        {filteredSyntheses.length > 0 ? (
          <div className="space-y-2">
            {filteredSyntheses.map((item, index) => (
              <div 
                key={index}
                className="p-5 hover:bg-surface-container-low/50 transition-colors flex flex-col gap-3 text-left rounded-2xl"
              >
                <div className="flex items-start justify-between gap-4">
                  <h4 className="font-semibold text-base sm:text-lg leading-snug text-on-surface">
                    {item.topic}
                  </h4>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] font-semibold bg-primary/10 text-primary px-3 py-1 rounded-full">
                      {item.category}
                    </span>
                    <span className="text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 px-3 py-1 rounded-full">
                      {item.status}
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs sm:text-sm text-on-surface-variant">
                  <span className="flex items-center gap-1.5">
                    <FileText size={15} className="text-primary/70" />
                    {item.papers} sources analyzed
                  </span>
                  <span className="text-outline-variant/60">•</span>
                  <span>Format: {item.style}</span>
                  <span className="sm:ml-auto text-[12px] sm:text-xs text-on-surface-variant/70">{item.date}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-8 text-center text-on-surface-variant text-sm sm:text-base">
            No syntheses match your criteria.
          </div>
        )}
      </div>
    </div>
  );
}
