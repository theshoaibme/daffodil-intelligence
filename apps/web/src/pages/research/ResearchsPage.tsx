import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Telescope, Search, BookOpen, Link2, Sparkles, MessageSquare, Database, History, CheckCircle2, FileText } from "lucide-react";
import { Button } from "@components/ui";
import { ROUTES } from "@lib";
import { PublicLayout } from "@layout";

export function ResearchsPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

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
        <div className="relative overflow-hidden py-4">
          <div className="flex flex-col sm:flex-row items-start gap-4 sm:gap-6 relative z-10">
            <div className="p-4 rounded-3xl bg-primary/10 text-primary shrink-0">
              <Telescope size={32} />
            </div>
            <div className="text-left flex-1">
              <span className="text-xs font-semibold tracking-wider text-primary uppercase bg-primary/10 px-2.5 py-1 rounded-full">
                Active
              </span>
              <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-3 mb-2 text-on-surface">
                Research & Literature Analysis
              </h1>
              <p className="text-on-surface-variant text-sm sm:text-base max-w-3xl leading-relaxed">
                Aggregate papers, extract academic citations, and synthesize findings automatically.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 2: Interactive Search, Category Filters, and Filtered Research Syntheses List */}
        <div className="space-y-6 sm:space-y-8 relative overflow-hidden">
          {/* Centered Search & Category Filter Section */}
          <div className="flex flex-col items-center gap-4 text-center relative z-10 max-w-2xl mx-auto">
            <div className="relative w-full">
              <Search
                size={18}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant/60 pointer-events-none"
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search recent syntheses by topic..."
                className="w-full bg-surface-container-low/85 rounded-full pl-11 pr-5 py-3 text-sm text-on-surface placeholder:text-on-surface-variant/75 focus:ring-2 focus:ring-primary/45 outline-none transition-all"
              />
            </div>
            
            <div className="flex flex-wrap justify-center gap-2 mt-1">
              {categories.map((cat) => {
                const isActive = selectedCategory === cat;
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-4 py-1.5 rounded-full text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer ${
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
            <h3 className="text-base font-semibold text-on-surface flex items-center gap-2 mb-2">
              <History className="text-primary" size={18} />
              Recent Syntheses
            </h3>
            
            {filteredSyntheses.length > 0 ? (
              <div className="space-y-1">
                {filteredSyntheses.map((item, index) => (
                  <div 
                    key={index}
                    className="p-4 hover:bg-surface-container-low/50 transition-colors flex flex-col gap-2.5 text-left rounded-xl"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="font-semibold text-sm leading-snug text-on-surface">
                        {item.topic}
                      </h4>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-[10px] font-semibold bg-primary/10 text-primary px-2.5 py-0.5 rounded-full">
                          {item.category}
                        </span>
                        <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 px-2.5 py-0.5 rounded-full">
                          {item.status}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-on-surface-variant">
                      <span className="flex items-center gap-1.5">
                        <FileText size={13} className="text-primary/70" />
                        {item.papers} sources analyzed
                      </span>
                      <span className="text-outline-variant/60">•</span>
                      <span>Format: {item.style}</span>
                      <span className="sm:ml-auto text-[11px] text-on-surface-variant/70">{item.date}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-on-surface-variant text-sm">
                No syntheses match your criteria.
              </div>
            )}
          </div>
        </div>

        {/* SECTION 3: Core Capabilities */}
        <div className="space-y-4 text-left relative overflow-hidden">
          <h2 className="text-base font-semibold text-on-surface flex items-center gap-2">
            <Sparkles size={18} className="text-primary" />
            Capabilities
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="p-5 flex flex-col">
              <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3 text-primary">
                <Search size={18} />
              </div>
              <h3 className="font-semibold text-sm mb-1 text-on-surface">Web Search</h3>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Crawl pages and extract references.
              </p>
            </div>

            <div className="p-5 flex flex-col">
              <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3 text-primary">
                <BookOpen size={18} />
              </div>
              <h3 className="font-semibold text-sm mb-1 text-on-surface">Paper Analysis</h3>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Analyze journals, PDFs, and verify facts.
              </p>
            </div>

            <div className="p-5 flex flex-col">
              <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3 text-primary">
                <Link2 size={18} />
              </div>
              <h3 className="font-semibold text-sm mb-1 text-on-surface">Citations</h3>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                Generate APA, IEEE, and Harvard references.
              </p>
            </div>
          </div>
        </div>

        {/* SECTION 4: Connected Academic Indexes */}
        <div className="space-y-4 relative overflow-hidden text-left">
          <h2 className="text-base font-semibold flex items-center gap-2">
            <Database className="text-primary" size={18} />
            Academic Indexes
          </h2>
          
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { name: "Google Scholar", description: "Literature & patents", status: "Connected", latency: "124ms" },
              { name: "arXiv Repository", description: "Physics & CS papers", status: "Connected", latency: "87ms" },
              { name: "IEEE Xplore", description: "CS & engineering articles", status: "Connected", latency: "145ms" },
              { name: "PubMed Central", description: "Biomedical database", status: "Available", latency: null },
            ].map((indexItem, index) => (
              <div 
                key={index}
                className="p-4 flex flex-col justify-between gap-3 text-left"
              >
                <div className="min-w-0">
                  <h3 className="font-medium text-sm leading-normal text-on-surface">{indexItem.name}</h3>
                  <p className="text-xs text-on-surface-variant/75 mt-1">{indexItem.description}</p>
                </div>
                
                <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-outline-variant/10">
                  <span className={`inline-flex items-center gap-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    indexItem.status === "Connected" 
                      ? "bg-emerald-500/10 text-emerald-600" 
                      : "bg-surface-container-high text-on-surface-variant/70"
                  }`}>
                    {indexItem.status === "Connected" && <CheckCircle2 size={10} />}
                    {indexItem.status}
                  </span>
                  {indexItem.latency && (
                    <span className="text-[10px] text-on-surface-variant/50">{indexItem.latency}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SECTION 5: Start Session Action Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 relative overflow-hidden py-4">
          <div className="flex items-center gap-2.5 text-sm text-on-surface-variant text-left">
            <Sparkles size={16} className="text-primary animate-pulse shrink-0" />
            <span>Ready to start? Select "Research" mode.</span>
          </div>
          <Button
            variant="contained"
            onClick={() => navigate(`${ROUTES.home}?agents=1`)}
            className="w-full sm:w-auto px-6 py-2.5 text-sm font-semibold rounded-full"
          >
            <MessageSquare size={16} className="mr-2" />
            Start Session
          </Button>
        </div>

      </main>
    </PublicLayout>
  );
}
