import { PublicLayout } from "@layout";
import { ResearchHeader } from "./components/ResearchHeader";
import { ResearchSearch } from "./components/ResearchSearch";
import { ResearchCapabilities } from "./components/ResearchCapabilities";
import { ResearchIndexes } from "./components/ResearchIndexes";
import { ResearchFooter } from "./components/ResearchFooter";

export function ResearchsPage() {
  return (
    <PublicLayout>
      <main className="max-w-[90rem] mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex-1 flex flex-col justify-center space-y-12 sm:space-y-16 animate-fadeIn">
        <ResearchHeader />
        <ResearchSearch />
        <ResearchCapabilities />
        <ResearchIndexes />
        <ResearchFooter />
      </main>
    </PublicLayout>
  );
}
