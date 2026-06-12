import { useEffect, useRef, useState } from "react";
import { BookOpen } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@ui";
import { ResearchPaper } from "./types";
import { PAPER_CATEGORIES } from "./paperStore";

export type PaperFormValues = Omit<ResearchPaper, "id" | "citations">;

interface PaperFormProps {
  initial?: ResearchPaper;
  submitLabel: string;
  onSubmit: (values: PaperFormValues) => void;
  onCancel?: () => void;
}

const emptyForm = (): PaperFormValues => ({
  title: "",
  authors: "",
  year: new Date().getFullYear().toString(),
  source: "",
  category: "Computer Science",
  abstract: "",
  url: "",
  pdfUrl: "",
  tags: [],
});

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
    tags: paper.tags ?? [],
  };
}

export function PaperForm({ initial, submitLabel, onSubmit, onCancel }: PaperFormProps) {
  const [form, setForm] = useState<PaperFormValues>(initial ? toFormValues(initial) : emptyForm());
  const [tagsInput, setTagsInput] = useState((initial?.tags ?? []).join(", "));
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initial) {
      setForm(toFormValues(initial));
      setTagsInput((initial.tags ?? []).join(", "));
    } else {
      setForm(emptyForm());
      setTagsInput("");
    }
    firstFieldRef.current?.focus();
  }, [initial]);

  const set =
    (field: keyof PaperFormValues) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.authors || !form.abstract) return;

    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    onSubmit({
      ...form,
      source: form.source || "Local Library",
      url: form.url?.trim() || undefined,
      pdfUrl: form.pdfUrl?.trim() || undefined,
      tags: tags.length > 0 ? tags : undefined,
    });
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
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Category
            </label>
            <Select
              value={form.category}
              onValueChange={(value) => setForm((prev) => ({ ...prev, category: value }))}
            >
              <SelectTrigger aria-label="Category">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {PAPER_CATEGORIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Paper URL{" "}
              <span className="text-on-surface-variant/40 font-normal">(optional)</span>
            </label>
            <input
              type="url"
              value={form.url}
              onChange={set("url")}
              placeholder="https://arxiv.org/abs/..."
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              PDF URL{" "}
              <span className="text-on-surface-variant/40 font-normal">(optional)</span>
            </label>
            <input
              type="url"
              value={form.pdfUrl}
              onChange={set("pdfUrl")}
              placeholder="https://arxiv.org/pdf/..."
              className={inputClass}
            />
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
