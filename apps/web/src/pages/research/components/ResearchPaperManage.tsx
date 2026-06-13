import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, LayoutGrid, List, Plus, Search } from "lucide-react";
import { ROUTES } from "@lib";
import { ResearchPaper } from "./types";
import {
  addPaper,
  deletePaper,
  generateId,
  getPapers,
  updatePaper,
} from "./paperStore";
import { PaperForm, PaperFormValues } from "./PaperForm";
import { ResearchPaperManageCard } from "./ResearchPaperManageCard";
import { ResearchPagination } from "./ResearchPagination";

type ViewMode = "grid" | "list";
const ITEMS_PER_PAGE = 9;

export function ResearchPaperManage() {
  const [papers, setPapers] = useState<ResearchPaper[]>(getPapers);
  const [searchQuery, setSearchQuery] = useState("");
  const [editingPaper, setEditingPaper] = useState<ResearchPaper | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [currentPage, setCurrentPage] = useState(1);
  const [isViewDropdownOpen, setIsViewDropdownOpen] = useState(false);
  const viewDropdownRef = useRef<HTMLDivElement>(null);

  const refresh = () => setPapers(getPapers());

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (viewDropdownRef.current && !viewDropdownRef.current.contains(event.target as Node)) {
        setIsViewDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

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

  const totalPages = Math.max(1, Math.ceil(filteredPapers.length / ITEMS_PER_PAGE));

  const currentItems = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredPapers.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredPapers, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, viewMode]);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

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
        {/* <p className="text-sm text-on-surface-variant max-w-2xl">
          Create, edit, and delete papers in your library. Changes here are reflected on the public
          research page.
        </p> */}
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
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <div className="relative flex-1 sm:flex-initial sm:max-w-xs">
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

            <div ref={viewDropdownRef} className="relative shrink-0">
              <button
                type="button"
                onClick={() => setIsViewDropdownOpen((v) => !v)}
                className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-surface-container-lowest text-on-surface-variant hover:bg-surface-container-high transition-colors text-sm font-medium cursor-pointer border-0"
              >
                {viewMode === "grid" ? <LayoutGrid size={15} /> : <List size={15} />}
                <span className="hidden sm:inline">{viewMode === "grid" ? "Grid" : "List"}</span>
                <ChevronDown
                  size={13}
                  className="transition-transform duration-200"
                  style={{ transform: isViewDropdownOpen ? "rotate(180deg)" : "rotate(0deg)" }}
                />
              </button>

              {isViewDropdownOpen && (
                <div className="absolute right-0 top-full mt-2 z-[60] rounded-2xl shadow-xl p-1.5 min-w-[128px] bg-surface-container-lowest border border-outline-variant/20">
                  <button
                    type="button"
                    onClick={() => {
                      setViewMode("grid");
                      setIsViewDropdownOpen(false);
                    }}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer border-0 text-left ${
                      viewMode === "grid"
                        ? "bg-primary/10 text-primary"
                        : "text-on-surface-variant hover:bg-surface-container-high"
                    }`}
                  >
                    <LayoutGrid size={14} />
                    Grid view
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setViewMode("list");
                      setIsViewDropdownOpen(false);
                    }}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer border-0 text-left ${
                      viewMode === "list"
                        ? "bg-primary/10 text-primary"
                        : "text-on-surface-variant hover:bg-surface-container-high"
                    }`}
                  >
                    <List size={14} />
                    List view
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {filteredPapers.length === 0 ? (
          <div className="p-10 text-center rounded-3xl bg-surface-container-low/50 text-on-surface-variant">
            {papers.length === 0
              ? "No papers yet. Click Create new paper to add your first one."
              : "No papers match your search."}
          </div>
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {currentItems.map((paper) => (
              <ResearchPaperManageCard
                key={paper.id}
                paper={paper}
                view="grid"
                onEdit={() => {
                  setEditingPaper(paper);
                  setShowCreateForm(false);
                }}
                onDelete={() => handleDelete(paper)}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {currentItems.map((paper) => (
              <ResearchPaperManageCard
                key={paper.id}
                paper={paper}
                view="list"
                onEdit={() => {
                  setEditingPaper(paper);
                  setShowCreateForm(false);
                }}
                onDelete={() => handleDelete(paper)}
              />
            ))}
          </div>
        )}

        {filteredPapers.length > ITEMS_PER_PAGE && (
          <div className="flex justify-center pt-4 border-t border-outline-variant/10">
            <ResearchPagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
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
