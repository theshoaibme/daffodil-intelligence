import { PublicLayout } from "@layout";
import { PUBLIC_LAYOUT_WIDTH } from "@lib";
import { ResearchHeader } from "./components/ResearchHeader";
import { ResearchSearch } from "./components/ResearchSearch";
import { ResearchCapabilities } from "./components/ResearchCapabilities";
import { ResearchFooter } from "./components/ResearchFooter";

export function ResearchsPage() {
  return (
    <PublicLayout>
      <main className={`${PUBLIC_LAYOUT_WIDTH} py-8 sm:py-12 flex-1 flex flex-col justify-center space-y-12 sm:space-y-16 animate-fadeIn`}>
        <ResearchHeader />
        <ResearchSearch />
        <ResearchCapabilities />
        <ResearchFooter />
      </main>
    </PublicLayout>
  );
}
