import React, { useState, useEffect, useRef } from "react";
import { X, BookOpen } from "lucide-react";
import { ResearchPaper } from "./types";
import { PAPER_CATEGORIES } from "./paperStore";

interface AddPaperModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (paper: Omit<ResearchPaper, "citations" | "id">) => void;
}

function useFormState() {
  const [form, setForm] = useState({
    title: "",
    authors: "",
    year: new Date().getFullYear().toString(),
    source: "",
    category: "Computer Science",
    abstract: "",
    url: "",
  });

  const reset = () =>
    setForm({
      title: "",
      authors: "",
      year: new Date().getFullYear().toString(),
      source: "",
      category: "Computer Science",
      abstract: "",
      url: "",
    });

  const set =
    (field: string) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((prev) => ({ ...prev, [field]: e.target.value }));

  return { form, set, reset };
}

export function AddPaperModal({ isOpen, onClose, onAdd }: AddPaperModalProps) {
  const { form, set, reset } = useFormState();
  const firstFieldRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => firstFieldRef.current?.focus(), 80);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen]);

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.authors || !form.abstract) return;
    onAdd({
      title: form.title,
      authors: form.authors,
      year: form.year,
      source: form.source || "Local Library",
      category: form.category,
      abstract: form.abstract,
      url: form.url || undefined,
    });
    reset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(26,27,36,0.5)" }}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div
        className="w-full max-w-xl bg-surface-container-lowest rounded-3xl shadow-2xl relative overflow-hidden"
        style={{ animation: "scaleIn 0.2s cubic-bezier(0.34,1.56,0.64,1)" }}
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-7 pt-6 pb-4 border-b border-outline-variant/10">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10">
              <BookOpen size={18} className="text-primary" />
            </div>
            <h3 className="text-base font-semibold text-on-surface">Add New Research Paper</h3>
          </div>
          <button
            onClick={handleClose}
            type="button"
            className="p-2 rounded-full hover:bg-surface-container-low text-on-surface-variant transition-colors cursor-pointer border-0"
          >
            <X size={17} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-7 py-5 space-y-4">
          {/* Title */}
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
              className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0"
            />
          </div>

          {/* Authors + Year */}
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
                className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0"
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
                className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0"
              />
            </div>
          </div>

          {/* Category + Publisher */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
                Category
              </label>
              <select
                value={form.category}
                onChange={set("category")}
                className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0 cursor-pointer"
              >
                {PAPER_CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
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
                className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0"
              />
            </div>
          </div>

          {/* URL */}
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
              className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0"
            />
          </div>

          {/* Abstract */}
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Abstract <span className="text-primary">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={form.abstract}
              onChange={set("abstract")}
              placeholder="Brief summary of the paper's key findings and contributions..."
              className="w-full px-4 py-2.5 rounded-xl bg-surface-container-low text-on-surface placeholder:text-on-surface-variant/40 focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all text-sm border-0 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2 pb-1">
            <button
              type="button"
              onClick={handleClose}
              className="px-5 py-2.5 rounded-full bg-surface-container-low text-on-surface-variant hover:bg-surface-container font-semibold text-sm transition-colors cursor-pointer border-0"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2.5 rounded-full bg-primary text-on-primary font-semibold text-sm hover:opacity-90 transition-opacity shadow-sm cursor-pointer border-0"
            >
              Add Paper
            </button>
          </div>
        </form>
      </div>

      <style>{`
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.94) translateY(8px); }
          to   { opacity: 1; transform: scale(1)    translateY(0);   }
        }
      `}</style>
    </div>
  );
}
