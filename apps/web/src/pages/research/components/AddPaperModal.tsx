import React, { useState } from "react";
import { X } from "lucide-react";
import { ResearchPaper } from "./types";

interface AddPaperModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (paper: Omit<ResearchPaper, "citations">) => void;
}

export function AddPaperModal({ isOpen, onClose, onAdd }: AddPaperModalProps) {
  const [newTitle, setNewTitle] = useState("");
  const [newAuthors, setNewAuthors] = useState("");
  const [newYear, setNewYear] = useState(new Date().getFullYear().toString());
  const [newSource, setNewSource] = useState("");
  const [newCategory, setNewCategory] = useState("Computer Science");
  const [newAbstract, setNewAbstract] = useState("");
  const [newUrl, setNewUrl] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newAuthors || !newAbstract) return;

    onAdd({
      title: newTitle,
      authors: newAuthors,
      year: newYear,
      source: newSource || "Local Library",
      category: newCategory,
      abstract: newAbstract,
      url: newUrl || undefined,
    });

    // Reset fields
    setNewTitle("");
    setNewAuthors("");
    setNewYear(new Date().getFullYear().toString());
    setNewSource("");
    setNewCategory("Computer Science");
    setNewAbstract("");
    setNewUrl("");
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/60 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-xl bg-surface-container-lowest rounded-3xl p-6 sm:p-8 shadow-2xl border border-outline-variant/20 relative animate-scaleIn">
        <button
          onClick={onClose}
          type="button"
          className="absolute right-5 top-5 p-2 rounded-full hover:bg-surface-container-low text-on-surface-variant transition-colors cursor-pointer border-0"
        >
          <X size={18} />
        </button>
        
        <h3 className="text-xl font-bold text-on-surface mb-6">Add New Research Paper</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4 text-left">
          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Paper Title *
            </label>
            <input
              type="text"
              required
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g. Attention Is All You Need"
              className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
                Authors *
              </label>
              <input
                type="text"
                required
                value={newAuthors}
                onChange={(e) => setNewAuthors(e.target.value)}
                placeholder="e.g. Vaswani et al."
                className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
                Publish Year *
              </label>
              <input
                type="number"
                required
                value={newYear}
                onChange={(e) => setNewYear(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
                Category *
              </label>
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all"
              >
                <option value="Computer Science">Computer Science</option>
                <option value="AI & Education">AI & Education</option>
                <option value="Smart Grids">Smart Grids</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
                Publisher / Journal
              </label>
              <input
                type="text"
                value={newSource}
                onChange={(e) => setNewSource(e.target.value)}
                placeholder="e.g. NeurIPS, arXiv"
                className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Paper URL (Optional)
            </label>
            <input
              type="url"
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              placeholder="https://arxiv.org/..."
              className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-on-surface-variant mb-1.5">
              Abstract *
            </label>
            <textarea
              required
              rows={3}
              value={newAbstract}
              onChange={(e) => setNewAbstract(e.target.value)}
              placeholder="Brief summary of the paper's findings..."
              className="w-full px-4 py-2.5 rounded-xl border border-outline-variant bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-transparent outline-none transition-all resize-none"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-full border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container-low font-semibold text-xs sm:text-sm transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-full bg-primary text-on-primary font-semibold text-xs sm:text-sm hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
            >
              Save Paper
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
