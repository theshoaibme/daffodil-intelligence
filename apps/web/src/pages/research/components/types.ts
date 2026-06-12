export interface ResearchPaper {
  id: string;
  title: string;
  authors: string;
  year: string;
  citations: number;
  source: string;
  category: string;
  abstract: string;
  url?: string;
  pdfUrl?: string;
  tags?: string[];
}
