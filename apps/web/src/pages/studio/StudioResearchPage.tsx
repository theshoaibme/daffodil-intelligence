import { StudioPageHeader } from "@layout";
import { ResearchPaperManage } from "../research/components/ResearchPaperManage";

export function StudioResearchPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <StudioPageHeader title="Research" borderless />
      <main className="max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex-1">
        <ResearchPaperManage />
      </main>
    </div>
  );
}
