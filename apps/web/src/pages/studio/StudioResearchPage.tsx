import { StudioPageHeader } from "@layout";
import { ResearchHeader } from "../research/components/ResearchHeader";
import { ResearchSearch } from "../research/components/ResearchSearch";
import { ResearchCapabilities } from "../research/components/ResearchCapabilities";
import { ResearchFooter } from "../research/components/ResearchFooter";

export function StudioResearchPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <StudioPageHeader title="Research" />
      <main className="max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex-1 flex flex-col justify-center space-y-12 sm:space-y-16">
        <ResearchHeader />
        <ResearchSearch />
        <ResearchCapabilities />
        <ResearchFooter />
      </main>
    </div>
  );
}
