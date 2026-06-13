import { ResearchPaper } from "../components/types";

/** Resolve a direct PDF URL for viewing or downloading the full paper. */
export function getPaperPdfUrl(paper: ResearchPaper): string | undefined {
  if (paper.pdfUrl) return paper.pdfUrl;

  const url = paper.url?.trim();
  if (!url) return undefined;

  if (/\.pdf(\?|#|$)/i.test(url)) return url;

  const arxivAbs = url.match(/arxiv\.org\/abs\/([^/?#]+)/i);
  if (arxivAbs) return `https://arxiv.org/pdf/${arxivAbs[1]}.pdf`;

  const arxivPdf = url.match(/arxiv\.org\/pdf\/([^/?#]+)/i);
  if (arxivPdf) {
    const id = arxivPdf[1].replace(/\.pdf$/i, "");
    return `https://arxiv.org/pdf/${id}.pdf`;
  }

  return undefined;
}

/** PDF URL that encourages the browser to download (arXiv supports ?download=1). */
export function getPaperPdfDownloadUrl(paper: ResearchPaper): string | undefined {
  const pdfUrl = getPaperPdfUrl(paper);
  if (!pdfUrl) return undefined;
  if (pdfUrl.includes("arxiv.org/pdf/")) {
    return `${pdfUrl}${pdfUrl.includes("?") ? "&" : "?"}download=1`;
  }
  return pdfUrl;
}

export function getPaperPdfFilename(paper: ResearchPaper): string {
  if (paper.pdfFileName) return paper.pdfFileName;
  const safe = paper.id.replace(/[^a-z0-9-]/gi, "-");
  return `${safe}.pdf`;
}

