import { getAuthHeaders } from "./api";
import type { ResearchPaper } from "../pages/research/components/types";

const API_BASE = import.meta.env.VITE_API_URL || "";

function url(path: string): string {
  return `${API_BASE.replace(/\/$/, "")}${path}`;
}

export interface ApiResearchPaper {
  id: string;
  title: string;
  authors: string;
  year: string;
  citations: number;
  source: string;
  category: string;
  abstract: string;
  url?: string | null;
  pdf_url?: string | null;
  pdf_file_name?: string | null;
  tags?: string[];
  is_public?: boolean;
}

export interface ResearchPaperListResponse {
  items: ApiResearchPaper[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ResearchCategoriesResponse {
  categories: string[];
  form_categories: string[];
}

export const CATEGORY_OTHERS = "Others";

export function mapResearchPaper(p: ApiResearchPaper): ResearchPaper {
  return {
    id: p.id,
    title: p.title,
    authors: p.authors,
    year: p.year,
    citations: p.citations ?? 0,
    source: p.source,
    category: p.category,
    abstract: p.abstract,
    url: p.url ?? undefined,
    pdfUrl: p.pdf_url ?? undefined,
    pdfFileName: p.pdf_file_name ?? undefined,
    tags: p.tags ?? [],
  };
}

async function publicRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url(path), init);
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

async function authRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url(path), {
    ...init,
    headers: { ...getAuthHeaders(), ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return {} as T;
  return res.json();
}

export type ResearchPaperInput = Omit<ResearchPaper, "id" | "citations"> & {
  citations?: number;
  isPublic?: boolean;
};

function toApiBody(data: ResearchPaperInput) {
  return {
    title: data.title,
    authors: data.authors,
    year: data.year,
    source: data.source,
    category: data.category,
    abstract: data.abstract,
    url: data.url,
    pdf_url: data.pdfUrl,
    pdf_file_name: data.pdfFileName,
    tags: data.tags,
    citations: data.citations ?? 0,
    is_public: data.isPublic ?? true,
  };
}

export const researchApi = {
  listCategories() {
    return publicRequest<ResearchCategoriesResponse>("/api/research/categories");
  },

  listPublic(params?: { category?: string; q?: string; page?: number; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.category && params.category !== "All") qs.set("category", params.category);
    if (params?.q) qs.set("q", params.q);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return publicRequest<ResearchPaperListResponse>(`/api/research/papers${q ? `?${q}` : ""}`);
  },

  getPublic(paperId: string) {
    return publicRequest<ApiResearchPaper>(`/api/research/papers/${encodeURIComponent(paperId)}`);
  },

  listManage(params?: { q?: string; page?: number; limit?: number }) {
    const qs = new URLSearchParams();
    if (params?.q) qs.set("q", params.q);
    if (params?.page) qs.set("page", String(params.page));
    if (params?.limit) qs.set("limit", String(params.limit));
    const q = qs.toString();
    return authRequest<ResearchPaperListResponse>(`/api/research/manage/papers${q ? `?${q}` : ""}`);
  },

  create(data: ResearchPaperInput) {
    return authRequest<ApiResearchPaper>("/api/research/papers", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toApiBody(data)),
    });
  },

  update(paperId: string, data: Partial<ResearchPaperInput>) {
    const body: Record<string, unknown> = {};
    if (data.title !== undefined) body.title = data.title;
    if (data.authors !== undefined) body.authors = data.authors;
    if (data.year !== undefined) body.year = data.year;
    if (data.source !== undefined) body.source = data.source;
    if (data.category !== undefined) body.category = data.category;
    if (data.abstract !== undefined) body.abstract = data.abstract;
    if (data.url !== undefined) body.url = data.url;
    if (data.pdfUrl !== undefined) body.pdf_url = data.pdfUrl;
    if (data.pdfFileName !== undefined) body.pdf_file_name = data.pdfFileName;
    if (data.tags !== undefined) body.tags = data.tags;
    if (data.citations !== undefined) body.citations = data.citations;
    if (data.isPublic !== undefined) body.is_public = data.isPublic;

    return authRequest<ApiResearchPaper>(`/api/research/papers/${encodeURIComponent(paperId)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },

  delete(paperId: string) {
    return authRequest<void>(`/api/research/papers/${encodeURIComponent(paperId)}`, {
      method: "DELETE",
    });
  },
};
