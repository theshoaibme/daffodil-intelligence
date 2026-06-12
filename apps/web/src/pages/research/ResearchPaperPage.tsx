import { Link, Navigate, useLocation, useParams } from "react-router-dom";
import { ArrowLeft, Award, ExternalLink, Tag } from "lucide-react";
import { PublicLayout, StudioPageHeader } from "@layout";
import { isStudioPath, PUBLIC_LAYOUT_WIDTH, ROUTES } from "@lib";
import { getPaperById } from "./components/paperStore";

export function ResearchPaperPage() {
  const { paperId } = useParams<{ paperId: string }>();
  const location = useLocation();
  const workspace = isStudioPath(location.pathname);
  const listPath = workspace ? ROUTES.research : ROUTES.publicResearchs;

  const paper = paperId ? getPaperById(decodeURIComponent(paperId)) : undefined;

  if (!paper) {
    return <Navigate to={listPath} replace />;
  }

  const content = (
    <main
      className={`${workspace ? "max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8" : PUBLIC_LAYOUT_WIDTH} py-8 sm:py-12 flex-1 animate-fadeIn`}
    >
      <Link
        to={listPath}
        className="inline-flex items-center gap-2 text-sm font-medium text-on-surface-variant hover:text-on-surface transition-colors mb-8"
      >
        <ArrowLeft size={16} />
        Back to research library
      </Link>

      <article className="w-full space-y-6">
          <div className="space-y-3">
            <span className="inline-flex text-[11px] font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-full">
              {paper.category}
            </span>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-on-surface leading-tight">
              {paper.title}
            </h1>
            <p className="text-base text-on-surface-variant italic">{paper.authors}</p>
            <div className="flex flex-wrap items-center gap-4 text-sm text-on-surface-variant/80">
              <span>{paper.year}</span>
              <span>•</span>
              <span>{paper.source}</span>
              <span>•</span>
              <span className="inline-flex items-center gap-1">
                <Award size={14} className="text-primary/70" />
                {paper.citations.toLocaleString()} citations
              </span>
            </div>
          </div>

          <section className="rounded-3xl bg-surface-container-low p-6 sm:p-8 space-y-4">
            <h2 className="text-lg font-semibold text-on-surface">Abstract</h2>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">
              {paper.abstract}
            </p>
          </section>

          {paper.tags && paper.tags.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-on-surface flex items-center gap-2">
                <Tag size={16} className="text-primary" />
                Topics
              </h2>
              <div className="flex flex-wrap gap-2">
                {paper.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 rounded-full text-xs font-medium bg-surface-container-low text-on-surface-variant"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </section>
          )}

          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              View original source
              <ExternalLink size={14} />
            </a>
          )}
      </article>
    </main>
  );

  if (workspace) {
    return (
      <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
        <StudioPageHeader title="Research" />
        {content}
      </div>
    );
  }

  return <PublicLayout>{content}</PublicLayout>;
}
