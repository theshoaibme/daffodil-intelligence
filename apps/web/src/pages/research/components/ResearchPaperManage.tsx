import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Eye, Pencil, Plus, Search, Trash2 } from "lucide-react";
import { researchPaperPath, ROUTES } from "@lib";
import { ResearchPaper } from "./types";
import {
  addPaper,
  deletePaper,
  generateId,
  getPapers,
  updatePaper,
} from "./paperStore";
import { PaperForm, PaperFormValues } from "./PaperForm";

export function ResearchPaperManage() {
  const [papers, setPapers] = useState<ResearchPaper[]>(getPapers);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingPaper, setEditingPaper] = useState<ResearchPaper | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(true);

  const refresh = () => setPapers(getPapers());

  const filteredPapers = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return papers;
    return papers.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        p.authors.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q) ||
        p.abstract.toLowerCase().includes(q),
    );
  }, [papers, searchQuery]);

  const handleCreate = (values: PaperFormValues) => {
    const newPaper: ResearchPaper = {
      ...values,
      id: generateId(values.title),
      citations: 0,
    };
    addPaper(newPaper);
    refresh();
    setShowCreateForm(false);
  };

  const handleUpdate = (values: PaperFormValues) => {
    if (!editingPaper) return;
    updatePaper(editingPaper.id, values);
    refresh();
    setEditingPaper(null);
  };

  const handleDelete = (paper: ResearchPaper) => {
    const confirmed = window.confirm(`Delete "${paper.title}"? This cannot be undone.`);
    if (!confirmed) return;
    deletePaper(paper.id);
    if (editingPaper?.id === paper.id) setEditingPaper(null);
    refresh();
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="space-y-2">
        <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-on-surface">
          Manage research papers
        </h2>
        <p className="text-sm text-on-surface-variant max-w-2xl">
          Create, edit, and delete papers in your library. Changes here are reflected on the public
          research page.
        </p>
      </div>

      {editingPaper ? (
        <PaperForm
          key={editingPaper.id}
          initial={editingPaper}
          submitLabel="Save changes"
          onSubmit={handleUpdate}
          onCancel={() => setEditingPaper(null)}
        />
      ) : showCreateForm ? (
        <PaperForm
          key="create"
          submitLabel="Create"
          onSubmit={handleCreate}
          onCancel={() => setShowCreateForm(false)}
        />
      ) : (
        <button
          type="button"
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-on-primary font-semibold text-sm hover:opacity-90 transition-opacity shadow-sm cursor-pointer border-0"
        >
          <Plus size={16} />
          Create new paper
        </button>
      )}

      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h3 className="text-lg font-semibold text-on-surface">
            Your library ({filteredPapers.length})
          </h3>
          <div className="relative w-full sm:max-w-xs">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60"
            />
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search papers..."
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm border-0 selection:bg-primary selection:text-on-primary autofill-light dark:autofill-dark"
            />
          </div>
        </div>

        {filteredPapers.length === 0 ? (
          <div className="p-10 text-center rounded-3xl bg-surface-container-low/50 text-on-surface-variant">
            {papers.length === 0
              ? "No papers yet. Create your first research paper above."
              : "No papers match your search."}
          </div>
        ) : (
          <div className="overflow-hidden rounded-3xl bg-surface-container-low">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead>
                  <tr className="text-left text-xs font-semibold text-on-surface-variant">
                    <th className="px-5 py-3">Title</th>
                    <th className="px-5 py-3">Authors</th>
                    <th className="px-5 py-3">Year</th>
                    <th className="px-5 py-3">Category</th>
                    <th className="px-5 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPapers.map((paper) => (
                    <tr
                      key={paper.id}
                      className="hover:bg-surface-container-high/40 transition-colors"
                    >
                      <td className="px-5 py-4 font-medium text-on-surface max-w-[240px]">
                        <span className="line-clamp-2">{paper.title}</span>
                      </td>
                      <td className="px-5 py-4 text-on-surface-variant max-w-[180px]">
                        <span className="line-clamp-1">{paper.authors}</span>
                      </td>
                      <td className="px-5 py-4 text-on-surface-variant whitespace-nowrap">
                        {paper.year}
                      </td>
                      <td className="px-5 py-4 whitespace-nowrap">
                        <span className="text-[11px] font-semibold text-primary bg-primary/10 px-2.5 py-1 rounded-full">
                          {paper.category}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center justify-end gap-1">
                          <Link
                            to={researchPaperPath(paper.id, { workspace: true })}
                            className="p-2 rounded-lg text-on-surface-variant hover:text-primary hover:bg-primary/10 transition-colors"
                            title="View paper"
                          >
                            <Eye size={16} />
                          </Link>
                          <button
                            type="button"
                            onClick={() => {
                              setEditingPaper(paper);
                              setShowCreateForm(false);
                            }}
                            className="p-2 rounded-lg text-on-surface-variant hover:text-primary hover:bg-primary/10 transition-colors cursor-pointer border-0"
                            title="Edit paper"
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(paper)}
                            className="p-2 rounded-lg text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors cursor-pointer border-0"
                            title="Delete paper"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-on-surface-variant/70">
        Browse the public library at{" "}
        <Link to={ROUTES.publicResearchs} className="text-primary font-medium hover:underline">
          /researchs
        </Link>
        .
      </p>
    </div>
  );
}
