import { Database, CheckCircle2 } from "lucide-react";

export function ResearchIndexes() {
  const indexes = [
    { name: "Google Scholar", description: "Literature & patents", status: "Connected", latency: "124ms" },
    { name: "arXiv Repository", description: "Physics & CS papers", status: "Connected", latency: "87ms" },
    { name: "IEEE Xplore", description: "CS & engineering articles", status: "Connected", latency: "145ms" },
    { name: "PubMed Central", description: "Biomedical database", status: "Available", latency: null },
  ];

  return (
    <div className="space-y-6 relative overflow-hidden text-left">
      <h2 className="text-lg sm:text-xl font-semibold flex items-center gap-2">
        <Database className="text-primary" size={20} />
        Academic Indexes
      </h2>
      
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {indexes.map((indexItem, index) => (
          <div 
            key={index}
            className="p-5 flex flex-col justify-between gap-4 text-left bg-surface-container-low/70 rounded-2xl transition-all duration-200 hover:bg-surface-container-low hover:shadow-sm"
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
  );
}
