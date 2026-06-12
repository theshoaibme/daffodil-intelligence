import { Search, BookOpen, Link2, Sparkles } from "lucide-react";

export function ResearchCapabilities() {
  return (
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
  );
}
