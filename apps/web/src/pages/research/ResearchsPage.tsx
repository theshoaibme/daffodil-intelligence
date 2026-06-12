import { useNavigate } from "react-router-dom";
import { Telescope, Search, BookOpen, Link2, Sparkles, MessageSquare, Database, History, CheckCircle2, FileText } from "lucide-react";
import { Button } from "@components/ui";
import { ROUTES } from "@lib";
import { Header } from "@layout";

export function ResearchsPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <Header />

      <main className="max-w-5xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-12 flex-1 flex flex-col justify-center">
        <div className="rounded-[2.5rem] bg-surface-container-lowest p-6 sm:p-10 shadow-sm relative overflow-hidden">
          {/* Subtle gradient accent */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-start gap-4 sm:gap-6 mb-8 relative z-10">
            <div className="p-4 rounded-3xl bg-primary/10 text-primary shrink-0">
              <Telescope size={32} />
            </div>
            <div>
              <span className="text-xs font-semibold tracking-wider text-primary uppercase bg-primary/10 px-2.5 py-1 rounded-full">
                Research Agent Active
              </span>
              <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-3 mb-2">
                Deep Research & Literature Analysis
              </h1>
              <p className="text-on-surface-variant text-sm sm:text-base max-w-2xl leading-relaxed">
                Conduct exhaustive web searches, aggregate research papers, extract academic citations, and synthesize findings automatically with the dedicated Research agent.
              </p>
            </div>
          </div>

          <div className="grid gap-8 lg:grid-cols-5 mt-8 relative z-10 text-left">
            {/* Left Main Content (3 Columns) */}
            <div className="lg:col-span-3 space-y-8">
              {/* Features section */}
              <div className="space-y-4">
                <h2 className="text-base font-semibold text-on-surface">Core Capabilities</h2>
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-3xl bg-surface-container-low/70 p-5 flex flex-col">
                    <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3 text-primary">
                      <Search size={18} />
                    </div>
                    <h3 className="font-semibold text-sm mb-1">Deep Web Search</h3>
                    <p className="text-xs text-on-surface-variant leading-relaxed">
                      Orchestrate queries, crawl pages, and extract references.
                    </p>
                  </div>

                  <div className="rounded-3xl bg-surface-container-low/70 p-5 flex flex-col">
                    <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3 text-primary">
                      <BookOpen size={18} />
                    </div>
                    <h3 className="font-semibold text-sm mb-1">Paper Analysis</h3>
                    <p className="text-xs text-on-surface-variant leading-relaxed">
                      Analyze books, journals, PDFs, and verify facts.
                    </p>
                  </div>

                  <div className="rounded-3xl bg-surface-container-low/70 p-5 flex flex-col">
                    <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center mb-3 text-primary">
                      <Link2 size={18} />
                    </div>
                    <h3 className="font-semibold text-sm mb-1">Citations</h3>
                    <p className="text-xs text-on-surface-variant leading-relaxed">
                      Generate APA, IEEE references automatically.
                    </p>
                  </div>
                </div>
              </div>

              {/* Recent Syntheses */}
              <div className="space-y-3">
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <History className="text-primary" size={18} />
                  Recent Research Syntheses
                </h2>
                <div className="bg-surface-container-low/30 rounded-3xl p-2 space-y-1">
                  {[
                    {
                      topic: "Impact of Large Language Models on Software Engineering Education",
                      papers: 14,
                      style: "APA 7th Edition",
                      status: "Synthesized",
                      date: "June 12, 2026",
                    },
                    {
                      topic: "Optimization of Campus Shuttle Routing using Deep Reinforcement Learning",
                      papers: 8,
                      style: "IEEE Style",
                      status: "Synthesized",
                      date: "June 10, 2026",
                    },
                    {
                      topic: "Comparison of Quantum Cryptography Protocols in Smart Grids",
                      papers: 22,
                      style: "IEEE Style",
                      status: "Synthesized",
                      date: "June 05, 2026",
                    },
                  ].map((item, index) => (
                    <div 
                      key={index}
                      className="p-4 rounded-2xl hover:bg-surface-container-high/40 transition-colors flex flex-col gap-2"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-medium text-sm leading-snug line-clamp-2 text-on-surface">
                          {item.topic}
                        </h3>
                        <span className="shrink-0 text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 px-2 py-0.5 rounded-full">
                          {item.status}
                        </span>
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-on-surface-variant/80">
                        <span className="flex items-center gap-1">
                          <FileText size={13} />
                          {item.papers} sources analyzed
                        </span>
                        <span>•</span>
                        <span>Format: {item.style}</span>
                        <span className="sm:ml-auto text-[11px] text-on-surface-variant/60">{item.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Side Control Panel (2 Columns) */}
            <div className="lg:col-span-2 space-y-6">
              {/* Action Box */}
              <div className="rounded-3xl bg-primary/5 p-6 space-y-4">
                <div className="flex items-center gap-2 text-primary">
                  <Sparkles size={20} className="animate-pulse" />
                  <span className="text-sm font-semibold">Start Research Workspace</span>
                </div>
                <p className="text-xs text-on-surface-variant leading-relaxed">
                  Select "Research" mode from the dashboard prompt bar to begin searching academic databases and generating literature syntheses.
                </p>
                <Button
                  variant="contained"
                  onClick={() => navigate(`${ROUTES.home}?agents=1`)}
                  className="w-full"
                >
                  <MessageSquare size={16} className="mr-2" />
                  Start Session
                </Button>
              </div>

              {/* Connected Indexes */}
              <div className="space-y-3">
                <h2 className="text-base font-semibold flex items-center gap-2">
                  <Database className="text-primary" size={18} />
                  Academic Indexes
                </h2>
                <div className="bg-surface-container-low/30 rounded-3xl p-2 space-y-1">
                  {[
                    { name: "Google Scholar", description: "Global literature & patents", status: "Connected", latency: "124ms" },
                    { name: "arXiv Repository", description: "Physics & CS preprints", status: "Connected", latency: "87ms" },
                    { name: "IEEE Xplore", description: "Electrical & CS library", status: "Connected", latency: "145ms" },
                    { name: "PubMed Central", description: "Biomedical database", status: "Available", latency: null },
                  ].map((indexItem, index) => (
                    <div 
                      key={index}
                      className="p-3.5 rounded-2xl hover:bg-surface-container-high/40 transition-colors flex items-center justify-between gap-3 text-left"
                    >
                      <div className="min-w-0">
                        <h3 className="font-medium text-sm leading-normal text-on-surface">{indexItem.name}</h3>
                        <p className="text-xs text-on-surface-variant/75 truncate mt-0.5">{indexItem.description}</p>
                      </div>
                      
                      <div className="shrink-0 flex flex-col items-end gap-1">
                        <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
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
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
