import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Telescope, Search, BookOpen, Link2, Sparkles, MessageSquare, Database, History, CheckCircle2, FileText } from "lucide-react";
import { Button } from "@components/ui";
import { ROUTES } from "@lib";
import { PublicLayout } from "@layout";

export function ResearchsPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

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

  const filteredSyntheses = researchSyntheses.filter((item) => {
    const matchesSearch = item.topic.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <PublicLayout>
      <main className="max-w-[90rem] mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex-1 flex flex-col justify-center space-y-12 sm:space-y-16 animate-fadeIn">
        
        {/* SECTION 1: Header / Title Block */}
        <div className="relative overflow-hidden py-4 text-center">
          <div className="flex flex-col items-center justify-center gap-4 relative z-10 max-w-4xl mx-auto">
            <div className="p-4 rounded-3xl bg-primary/10 text-primary">
              <Telescope size={40} />
            </div>
            <div className="flex flex-col items-center text-center">
              <span className="text-xs sm:text-sm font-semibold tracking-wider text-primary uppercase bg-primary/10 px-3 py-1 rounded-full w-fit">
                Active
              </span>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight mt-4 mb-3 text-on-surface text-center">
                Research & Literature Analysis
              </h1>
              <p className="text-on-surface-variant text-base sm:text-lg max-w-2xl mx-auto leading-relaxed text-center">
                Aggregate papers, extract academic citations, and synthesize findings automatically.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 2: Interactive Search, Category Filters, and Filtered Research Syntheses List */}
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

              {/* Dropdown Menu */}
              {isDropdownOpen && (
                <div className="absolute left-0 right-0 top-full mt-2 z-50 bg-surface-container-lowest rounded-3xl shadow-xl border border-outline-variant/10 p-5 space-y-4 text-left animate-fadeIn">
                  
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
                          className="px-3.5 py-1.5 rounded-full text-xs font-medium bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high transition-colors border-0 cursor-pointer"
                        >
                          {term}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="border-t border-outline-variant/10" />

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
                        className="w-full text-left px-3 py-2 rounded-xl text-xs sm:text-sm text-on-surface hover:bg-surface-container-low transition-colors block truncate border-0 cursor-pointer"
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

        {/* SECTION 3: Core Capabilities */}
        <div className="space-y-6 text-left relative overflow-hidden">
          <h2 className="text-lg sm:text-xl font-semibold text-on-surface flex items-center gap-2">
            <Sparkles size={20} className="text-primary" />
            Capabilities
          </h2>
          <div className="grid gap-6 sm:grid-cols-3">
            <div className="p-5 flex flex-col">
              <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <Search size={20} />
              </div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-on-surface">Web Search</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Crawl pages and extract references.
              </p>
            </div>

            <div className="p-5 flex flex-col">
              <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <BookOpen size={20} />
              </div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-on-surface">Paper Analysis</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Analyze journals, PDFs, and verify facts.
              </p>
            </div>

            <div className="p-5 flex flex-col">
              <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <Link2 size={20} />
              </div>
              <h3 className="font-semibold text-base sm:text-lg mb-2 text-on-surface">Citations</h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                Generate APA, IEEE, and Harvard references.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 4: Connected Academic Indexes */}
        <div className="space-y-6 relative overflow-hidden text-left">
          <h2 className="text-lg sm:text-xl font-semibold flex items-center gap-2">
            <Database className="text-primary" size={20} />
            Academic Indexes
          </h2>
          
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { name: "Google Scholar", description: "Literature & patents", status: "Connected", latency: "124ms" },
              { name: "arXiv Repository", description: "Physics & CS papers", status: "Connected", latency: "87ms" },
              { name: "IEEE Xplore", description: "CS & engineering articles", status: "Connected", latency: "145ms" },
              { name: "PubMed Central", description: "Biomedical database", status: "Available", latency: null },
            ].map((indexItem, index) => (
              <div 
                key={index}
                className="p-5 flex flex-col justify-between gap-4 text-left"
              >
                <div className="min-w-0">
                  <h3 className="font-semibold text-base text-on-surface">{indexItem.name}</h3>
                  <p className="text-sm text-on-surface-variant/80 mt-1.5">{indexItem.description}</p>
                </div>
                
                <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-outline-variant/10">
                  <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full ${
                    indexItem.status === "Connected" 
                      ? "bg-emerald-500/10 text-emerald-600" 
                      : "bg-surface-container-high text-on-surface-variant/70"
                  }`}>
                    {indexItem.status === "Connected" && <CheckCircle2 size={11} />}
                    {indexItem.status}
                  </span>
                  {indexItem.latency && (
                    <span className="text-[11px] text-on-surface-variant/50">{indexItem.latency}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION 5: Start Session Action Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6 relative overflow-hidden py-6">
          <div className="flex items-center gap-3 text-sm sm:text-base text-on-surface-variant text-left">
            <Sparkles size={18} className="text-primary animate-pulse shrink-0" />
            <span>Ready to start? Select "Research" mode.</span>
          </div>
          <Button
            variant="contained"
            onClick={() => navigate(`${ROUTES.home}?agents=1`)}
            className="w-full sm:w-auto px-8 py-3 text-sm sm:text-base font-semibold rounded-full"
          >
            <MessageSquare size={18} className="mr-2" />
            Start Session
          </Button>
        </div>

      </main>
    </PublicLayout>
  );
}
