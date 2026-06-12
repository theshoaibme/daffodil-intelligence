import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Header } from "@layout";
import { ROUTES } from "@lib";
import { ResearchPaperManage } from "../research/components/ResearchPaperManage";

export function StudioResearchPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
      <Header />
      <main className="max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 flex-1">
        <Link
          to={ROUTES.home}
          className="inline-flex items-center gap-2 text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors mb-6"
        >
          <ArrowLeft size={16} />
          Back to studio
        </Link>
        <ResearchPaperManage />
      </main>
    </div>
  );
}
