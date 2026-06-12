import { useNavigate } from "react-router-dom";
import { Telescope, ArrowLeft, Search, BookOpen, Link2, Sparkles, MessageSquare } from "lucide-react";
import { Button } from "@components/ui";
import { ROUTES } from "@lib";

export function ResearchsPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <header className="border-b border-outline-variant/40 bg-surface-container-lowest/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 hover:bg-surface-container-high rounded-full text-on-surface-variant hover:text-on-surface transition-colors border-0 bg-transparent cursor-pointer"
              title="Back"
            >
              <ArrowLeft size={20} />
            </button>
            <span className="font-semibold text-lg flex items-center gap-2">
              <Telescope className="text-primary" size={20} />
              Researchs Workspace
            </span>
          </div>
          <Button variant="outlined" size="sm" onClick={() => navigate(ROUTES.home)}>
            Go to chat
          </Button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-12 flex-1 flex flex-col justify-center">
        <div className="rounded-[2.5rem] border border-outline-variant/40 bg-surface-container-lowest p-6 sm:p-10 shadow-sm relative overflow-hidden">
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

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 mt-8 relative z-10">
            <div className="rounded-3xl border border-outline-variant/30 bg-surface-container-low/60 p-6 flex flex-col">
              <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <Search size={20} />
              </div>
              <h2 className="font-semibold text-base mb-1.5">Deep Web Search</h2>
              <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed flex-1">
                Orchestrate multiple search queries, crawl target websites, and pull reliable academic references.
              </p>
            </div>

            <div className="rounded-3xl border border-outline-variant/30 bg-surface-container-low/60 p-6 flex flex-col">
              <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <BookOpen size={20} />
              </div>
              <h2 className="font-semibold text-base mb-1.5">Paper Analysis</h2>
              <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed flex-1">
                Analyze books, journals, PDFs, and thesis drafts. Organize structure and cross-verify facts.
              </p>
            </div>

            <div className="rounded-3xl border border-outline-variant/30 bg-surface-container-low/60 p-6 flex flex-col">
              <div className="w-10 h-10 rounded-2xl bg-primary/10 flex items-center justify-center mb-4 text-primary">
                <Link2 size={20} />
              </div>
              <h2 className="font-semibold text-base mb-1.5">Citations & References</h2>
              <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed flex-1">
                Generate proper academic citations, manage references, and prevent formatting inconsistencies.
              </p>
            </div>
          </div>

          <div className="mt-10 pt-6 border-t border-outline-variant/20 flex flex-col sm:flex-row items-center justify-between gap-4 relative z-10">
            <div className="flex items-center gap-2 text-sm text-on-surface-variant">
              <Sparkles size={16} className="text-primary animate-pulse" />
              <span>Ready to start? Select "Research" mode from the dashboard prompt bar.</span>
            </div>
            <Button
              variant="contained"
              onClick={() => navigate(`${ROUTES.home}?agents=1`)}
              className="w-full sm:w-auto"
            >
              <MessageSquare size={16} className="mr-2" />
              Start Research Session
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
