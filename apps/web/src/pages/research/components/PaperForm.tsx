import { useEffect, useRef, useState } from "react";
import { BookOpen, FileUp, Link2, Upload, X } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@ui";
import { CATEGORY_OTHERS } from "@lib/researchApi";
import { ResearchPaper } from "./types";

export type PaperFormValues = Omit<ResearchPaper, "id" | "citations">;

interface PaperFormProps {
  initial?: ResearchPaper;
  submitLabel: string;
  formCategories: string[];
  onSubmit: (values: PaperFormValues) => void;
  onCancel?: () => void;
}

function resolveCategoryChoice(category: string, presetCategories: string[]): {
  choice: string;
  custom: string;
} {
  if (!category) return { choice: "", custom: "" };
  if (presetCategories.includes(category)) return { choice: category, custom: "" };
  return { choice: CATEGORY_OTHERS, custom: category };
}

const emptyForm = (): PaperFormValues => ({
  title: "",
  authors: "",
  year: new Date().getFullYear().toString(),
  source: "",
  category: "",
  abstract: "",
  url: "",
  pdfUrl: "",
  tags: [],
});

const MAX_PDF_BYTES = 10 * 1024 * 1024;

function isUploadedPdfUrl(value?: string): boolean {
  return Boolean(value?.startsWith("data:application/pdf"));
}

function toFormValues(paper: ResearchPaper): PaperFormValues {
  return {
    title: paper.title,
    authors: paper.authors,
    year: paper.year,
    source: paper.source,
    category: paper.category,
    abstract: paper.abstract,
    url: paper.url ?? "",
    pdfUrl: paper.pdfUrl ?? "",
    pdfFileName: paper.pdfFileName,
    tags: paper.tags ?? [],
  };
}

export function PaperForm({ initial, submitLabel, formCategories, onSubmit, onCancel }: PaperFormProps) {
  const presetCategories = formCategories.filter((c) => c !== CATEGORY_OTHERS);
  const [form, setForm] = useState<PaperFormValues>(initial ? toFormValues(initial) : emptyForm());
  const [tagsInput, setTagsInput] = useState((initial?.tags ?? []).join(", "));
  const [uploadedPdfName, setUploadedPdfName] = useState<string | null>(
    initial?.pdfFileName ?? (isUploadedPdfUrl(initial?.pdfUrl) ? "Uploaded PDF" : null),
  );
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [categoryChoice, setCategoryChoice] = useState(() =>
    resolveCategoryChoice(initial?.category ?? "", presetCategories).choice,
  );
  const [customCategory, setCustomCategory] = useState(() =>
    resolveCategoryChoice(initial?.category ?? "", presetCategories).custom,
  );
  const [categoryError, setCategoryError] = useState<string | null>(null);
  const firstFieldRef = useRef<HTMLInputElement>(null);
  const pdfInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initial) {
      setForm(toFormValues(initial));
      setTagsInput((initial.tags ?? []).join(", "));
      setUploadedPdfName(
        initial.pdfFileName ?? (isUploadedPdfUrl(initial.pdfUrl) ? "Uploaded PDF" : null),
      );
      const { choice, custom } = resolveCategoryChoice(initial.category, presetCategories);
      setCategoryChoice(choice);
      setCustomCategory(custom);
    } else {
      setForm(emptyForm());
      setTagsInput("");
      setUploadedPdfName(null);
      setCategoryChoice("");
      setCustomCategory("");
    }
    setPdfError(null);
    setCategoryError(null);
    if (pdfInputRef.current) pdfInputRef.current.value = "";
    firstFieldRef.current?.focus();
  }, [initial, presetCategories.join("|")]);

  const set =
    (field: keyof PaperFormValues) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.authors || !form.abstract) return;

    const category =
      categoryChoice === CATEGORY_OTHERS ? customCategory.trim() : categoryChoice.trim();

    if (!category) {
      setCategoryError(
        categoryChoice === CATEGORY_OTHERS
          ? "Please enter a custom category."
          : "Please select a category.",
      );
      return;
    }

    setCategoryError(null);

    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    onSubmit({
      ...form,
      category,
      source: form.source || "Local Library",
      url: form.url?.trim() || undefined,
      pdfUrl: form.pdfUrl?.trim() || undefined,
      pdfFileName: uploadedPdfName ?? undefined,
      tags: tags.length > 0 ? tags : undefined,
    });
  };

  const handlePdfFile = (file: File | null) => {
    if (!file) return;

    const isPdf =
      file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      setPdfError("Please upload a PDF file.");
      return;
    }
    if (file.size > MAX_PDF_BYTES) {
      setPdfError("PDF must be 10MB or smaller.");
      return;
    }

    setPdfError(null);
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result !== "string") return;
      setForm((prev) => ({ ...prev, pdfUrl: reader.result as string }));
      setUploadedPdfName(file.name);
    };
    reader.onerror = () => setPdfError("Failed to read PDF file.");
    reader.readAsDataURL(file);
  };

  const clearUploadedPdf = () => {
    setForm((prev) => ({ ...prev, pdfUrl: "" }));
    setUploadedPdfName(null);
    setPdfError(null);
    if (pdfInputRef.current) pdfInputRef.current.value = "";
  };

  const handlePdfUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadedPdfName(null);
    setPdfError(null);
    setForm((prev) => ({ ...prev, pdfUrl: e.target.value }));
  };

  const fieldClass =
    "bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0 selection:bg-primary selection:text-on-primary autofill-light dark:autofill-dark";

  const inputClass = `w-full px-4 py-2.5 rounded-xl ${fieldClass}`;

  const textareaClass = `block w-full min-h-[140px] px-4 py-3 rounded-2xl resize-y leading-relaxed ${fieldClass}`;

  return (
    <div className="rounded-3xl bg-surface-container-low">
      <div className="flex items-center gap-3 px-6 sm:px-8 pt-6 pb-4">
        <div className="p-2 rounded-xl bg-primary/10">
          <BookOpen size={18} className="text-primary" />
        </div>
        <h3 className="text-base font-semibold text-on-surface">
          {initial ? "Edit research paper" : "Create research paper"}
        </h3>
      </div>

      <form onSubmit={handleSubmit} className="px-6 sm:px-8 py-5 space-y-4">
        <div>
          <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
            Paper Title <span className="text-primary">*</span>
          </label>
          <input
            ref={firstFieldRef}
            type="text"
            required
            value={form.title}
            onChange={set("title")}
            placeholder="e.g. Attention Is All You Need"
            className={inputClass}
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Authors <span className="text-primary">*</span>
            </label>
            <input
              type="text"
              required
              value={form.authors}
              onChange={set("authors")}
              placeholder="e.g. Vaswani et al."
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Publish Year
            </label>
            <input
              type="number"
              value={form.year}
              onChange={set("year")}
              min="1900"
              max={new Date().getFullYear() + 1}
              className={inputClass}
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-3">
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Category <span className="text-primary">*</span>
            </label>
            <Select
              value={categoryChoice || undefined}
              onValueChange={(value) => {
                setCategoryChoice(value);
                setCategoryError(null);
                if (value !== CATEGORY_OTHERS) {
                  setCustomCategory("");
                  setForm((prev) => ({ ...prev, category: value }));
                } else {
                  setForm((prev) => ({ ...prev, category: "" }));
                }
              }}
            >
              <SelectTrigger aria-label="Category" aria-required="true">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {formCategories.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {categoryChoice === CATEGORY_OTHERS && (
              <input
                type="text"
                required
                value={customCategory}
                onChange={(e) => {
                  setCustomCategory(e.target.value);
                  setCategoryError(null);
                }}
                placeholder="Enter custom category"
                className={inputClass}
              />
            )}
            {categoryError && <p className="text-xs text-error">{categoryError}</p>}
          </div>
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Publisher / Journal
            </label>
            <input
              type="text"
              value={form.source}
              onChange={set("source")}
              placeholder="e.g. NeurIPS, arXiv"
              className={inputClass}
            />
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              <span className="inline-flex items-center gap-1.5">
                <Link2 size={14} className="text-primary/80" />
                Paper link{" "}
                <span className="text-on-surface-variant/40 font-normal">(optional)</span>
              </span>
            </label>
            <input
              type="url"
              value={form.url}
              onChange={set("url")}
              placeholder="https://arxiv.org/abs/..."
              className={inputClass}
            />
          </div>

          <div className="space-y-3">
            <label className="block text-xs font-semibold text-on-surface-variant">
              PDF{" "}
              <span className="text-on-surface-variant/40 font-normal">(upload or link)</span>
            </label>

            <input
              ref={pdfInputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="hidden"
              onChange={(e) => handlePdfFile(e.target.files?.[0] ?? null)}
            />

            {uploadedPdfName ? (
              <div className="flex items-center justify-between gap-3 rounded-2xl bg-surface-container-lowest px-4 py-3">
                <div className="flex items-center gap-2 min-w-0">
                  <FileUp size={16} className="text-primary shrink-0" />
                  <span className="text-sm text-on-surface truncate">{uploadedPdfName}</span>
                </div>
                <button
                  type="button"
                  onClick={clearUploadedPdf}
                  className="p-1.5 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer border-0"
                  aria-label="Remove uploaded PDF"
                >
                  <X size={14} />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => pdfInputRef.current?.click()}
                className="w-full flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-outline-variant/40 bg-surface-container-lowest px-4 py-6 text-on-surface-variant hover:text-on-surface hover:border-primary/40 hover:bg-surface-container-high/30 transition-colors cursor-pointer"
              >
                <Upload size={20} className="text-primary" />
                <span className="text-sm font-medium text-on-surface">Upload PDF</span>
                <span className="text-xs text-on-surface-variant/70">Max 10MB</span>
              </button>
            )}

            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-outline-variant/20" />
              <span className="text-xs text-on-surface-variant/60">or paste link</span>
              <div className="h-px flex-1 bg-outline-variant/20" />
            </div>

            <input
              type="url"
              value={isUploadedPdfUrl(form.pdfUrl) ? "" : form.pdfUrl}
              onChange={handlePdfUrlChange}
              placeholder="https://arxiv.org/pdf/..."
              className={`${inputClass} disabled:opacity-50 disabled:cursor-not-allowed`}
              disabled={Boolean(uploadedPdfName)}
            />

            {pdfError && <p className="text-xs text-error">{pdfError}</p>}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
            Topics{" "}
            <span className="text-on-surface-variant/40 font-normal">(comma-separated)</span>
          </label>
          <input
            type="text"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="e.g. transformer, NLP, attention"
            className={inputClass}
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
            Abstract <span className="text-primary">*</span>
          </label>
          <textarea
            required
            rows={5}
            value={form.abstract}
            onChange={set("abstract")}
            placeholder="Brief summary of the paper's key findings and contributions..."
            className={textareaClass}
          />
        </div>

        <div className="flex justify-end gap-3 pt-2 pb-1">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-5 py-2.5 rounded-full bg-surface-container-high text-on-surface hover:bg-surface-container-highest font-semibold text-sm transition-colors cursor-pointer border-0"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className="px-6 py-2.5 rounded-full bg-primary text-on-primary font-semibold text-sm hover:opacity-90 transition-opacity shadow-sm cursor-pointer border-0"
          >
            {submitLabel}
          </button>
        </div>
      </form>
    </div>
  );
}
