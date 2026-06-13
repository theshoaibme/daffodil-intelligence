import { useEffect, useState } from "react";
import { Link, Navigate, useLocation, useParams } from "react-router-dom";
import { ArrowLeft, Award, Download, ExternalLink, FileText, Tag } from "lucide-react";
import { Header, PublicLayout } from "@layout";
import { Loader } from "@ui";
import { isStudioPath, mapResearchPaper, PUBLIC_LAYOUT_WIDTH, researchApi, ROUTES } from "@lib";
import { ResearchPaper } from "./components/types";
import {
  getPaperPdfDownloadUrl,
  getPaperPdfFilename,
  getPaperPdfUrl,
} from "./lib/paperPdf";

export function ResearchPaperPage() {
  const { paperId } = useParams<{ paperId: string }>();
  const location = useLocation();
  const workspace = isStudioPath(location.pathname);
  const listPath = workspace ? ROUTES.research : ROUTES.publicResearchs;
  const [paper, setPaper] = useState<ResearchPaper | undefined>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!paperId) {
      setPaper(undefined);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    researchApi
      .getPublic(decodeURIComponent(paperId))
      .then((res) => {
        if (!cancelled) setPaper(mapResearchPaper(res));
      })
      .catch(() => {
        if (!cancelled) setPaper(undefined);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [paperId]);

  if (loading) {
    const shell = (
      <main
        className={`${workspace ? "max-w-6xl mx-auto w-full px-4 sm:px-6 lg:px-8" : PUBLIC_LAYOUT_WIDTH} py-8 sm:py-12 flex-1 animate-fadeIn flex items-center justify-center min-h-[40vh]`}
      >
        <Loader variant="spinner" diameter={36} strokeWidth={3} color="primary" message="Loading paper..." />
      </main>
    );
    if (workspace) {
      return (
        <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
          <Header />
          {shell}
        </div>
      );
    }
    return <PublicLayout>{shell}</PublicLayout>;
  }

  if (!paper) {
    return <Navigate to={listPath} replace />;
  }

  const pdfUrl = getPaperPdfUrl(paper);
  const pdfDownloadUrl = getPaperPdfDownloadUrl(paper);
  const pdfFilename = getPaperPdfFilename(paper);

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
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight text-on-surface leading-tight break-words">
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
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed break-words overflow-hidden">
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

          {(pdfUrl || paper.url) && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-on-surface flex items-center gap-2">
                <FileText size={16} className="text-primary" />
                Access paper
              </h2>
              <div className="flex flex-wrap gap-3">
                {pdfUrl && (
                  <>
                    <a
                      href={pdfUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary text-sm font-semibold hover:opacity-90 transition-opacity"
                    >
                      View PDF
                      <ExternalLink size={14} />
                    </a>
                    {pdfDownloadUrl && (
                      <a
                        href={pdfDownloadUrl}
                        download={pdfFilename}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-surface-container-low text-on-surface text-sm font-semibold hover:bg-surface-container transition-colors"
                      >
                        Download PDF
                        <Download size={14} />
                      </a>
                    )}
                  </>
                )}
                {paper.url && (
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-surface-container-low text-on-surface text-sm font-semibold hover:bg-surface-container transition-colors"
                  >
                    {pdfUrl ? "Original source" : "View original source"}
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </section>
          )}

          {pdfUrl && (
            <section className="space-y-3">
              <h2 className="text-lg font-semibold text-on-surface">Full paper</h2>
              <div className="rounded-3xl border border-outline-variant/15 bg-surface-container-lowest overflow-hidden">
                <object
                  data={pdfUrl}
                  type="application/pdf"
                  aria-label={`${paper.title} — PDF`}
                  className="w-full min-h-[70vh] sm:min-h-[80vh] bg-white block"
                >
                  <iframe
                    title={`${paper.title} — PDF`}
                    src={pdfUrl}
                    className="w-full min-h-[70vh] sm:min-h-[80vh] bg-white"
                  />
                </object>
              </div>
              <p className="text-xs text-on-surface-variant/70">
                PDF not loading?{" "}
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary font-medium hover:underline"
                >
                  Open the full paper in a new tab
                </a>
                .
              </p>
            </section>
          )}
      </article>
    </main>
  );

  if (workspace) {
    return (
      <div className="min-h-screen bg-background text-on-surface font-sans flex flex-col">
        <Header />
        {content}
      </div>
    );
  }

  return <PublicLayout>{content}</PublicLayout>;
}
