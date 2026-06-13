import { useState, useEffect, useRef, useCallback } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { isStudioPath, mapResearchPaper, researchApi, researchPaperPath, ROUTES } from "@lib";
import { FileText, Plus, LayoutGrid, List, ChevronDown } from "lucide-react";
import { ResearchPaper } from "./types";
import { ResearchPaperCard } from "./ResearchPaperCard";
import { ResearchDropdown } from "./ResearchDropdown";
import { ResearchPagination } from "./ResearchPagination";
import { Loader, PlaceholdersAndVanishInput } from "@ui";
import { useResearchCategories } from "../hooks/useResearchCategories";

type ViewMode = "grid" | "list";

export function ResearchSearch() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const workspace = isStudioPath(location.pathname);
  const { filterCategories } = useResearchCategories();
  const initialCategory = searchParams.get("category") || "All";
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState(
    filterCategories.includes(initialCategory) ? initialCategory : "All",
  );
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [isViewDropdownOpen, setIsViewDropdownOpen] = useState(false);
  const [papers, setPapers] = useState<ResearchPaper[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [dropdownPapers, setDropdownPapers] = useState<ResearchPaper[]>([]);

  const searchRef = useRef<HTMLDivElement>(null);
  const viewDropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (filterCategories.includes(initialCategory)) {
      setSelectedCategory(initialCategory);
    }
  }, [initialCategory, filterCategories]);

  const loadPapers = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await researchApi.listPublic({
        category: selectedCategory,
        q: searchQuery.trim() || undefined,
        page: currentPage,
        limit: 16,
      });
      setPapers(res.items.map(mapResearchPaper));
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      setPapers([]);
      setTotal(0);
      setTotalPages(1);
      setLoadError(err instanceof Error ? err.message : "Failed to load papers");
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, currentPage]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadPapers();
    }, searchQuery ? 300 : 0);
    return () => clearTimeout(timer);
  }, [loadPapers]);

  useEffect(() => {
    if (!isDropdownOpen) return;
    let cancelled = false;
    const timer = setTimeout(async () => {
      try {
        const res = await researchApi.listPublic({
          category: selectedCategory,
          q: searchQuery.trim() || undefined,
          page: 1,
          limit: 20,
        });
        if (!cancelled) setDropdownPapers(res.items.map(mapResearchPaper));
      } catch {
        if (!cancelled) setDropdownPapers([]);
      }
    }, 200);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [isDropdownOpen, searchQuery, selectedCategory]);

  const topSearches = [
    "Deep Learning",
    "Smart Grids Optimization",
    "Quantum Computing",
    "Protein Structure Prediction",
    "Robotic Control",
  ];

  const recentResearchSearches = [
    "Attention Is All You Need",
    "BERT: Pre-training of Deep Bidirectional Transformers",
    "Comparison of Quantum Cryptography Protocols in Smart Grids",
    "AlphaFold Protein Structure Prediction",
  ];

  // Close search dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Close view dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (viewDropdownRef.current && !viewDropdownRef.current.contains(event.target as Node)) {
        setIsViewDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredPapers = dropdownPapers;

  // Reset page to 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory]);

  const currentItems = papers;

  const handleAddPaper = () => {
    navigate(ROUTES.research);
  };

  const handleSelectSearch = (term: string) => {
    setSearchQuery(term);
    setIsDropdownOpen(false);
  };

  const handleOpenPaper = (paperId: string) => {
    setIsDropdownOpen(false);
    navigate(researchPaperPath(paperId, { workspace }));
  };

  const activeCategories = filterCategories;

  return (
    <div className="space-y-6 sm:space-y-8 relative">
      {/* Centered Search & Category Filter Section */}
      <div className="flex flex-col items-center gap-4 text-center relative z-20 max-w-2xl mx-auto">
        <div ref={searchRef} className="relative w-full">
          <PlaceholdersAndVanishInput
            placeholders={[
              "Search papers — then click View Paper to explore details in our research space",
              "e.g. Attention Is All You Need",
              "To view a paper's details, search here and open it from the results",
              "e.g. Protein structure prediction with AlphaFold",
              "e.g. Quantum Cryptography in Smart Grids",
            ]}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setIsDropdownOpen(true)}
            onSubmit={() => setIsDropdownOpen(false)}
          />

          {isDropdownOpen && (
            <ResearchDropdown
              topSearches={topSearches}
              recentResearchSearches={recentResearchSearches}
              onSelectSearch={handleSelectSearch}
              onOpenPaper={handleOpenPaper}
              searchResults={filteredPapers}
              searchQuery={searchQuery}
            />
          )}
        </div>

        {/* Category filter pills — smaller size */}
        <div className="flex flex-wrap justify-center gap-1.5 mt-1">
          {activeCategories.map((cat) => {
            const isActive = selectedCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-full text-[11px] sm:text-xs font-semibold transition-all duration-200 cursor-pointer border-0 ${
                  isActive
                    ? "bg-primary text-on-primary shadow-sm scale-105"
                    : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>
      </div>

      {/* Library Header Row */}
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-lg sm:text-xl font-semibold text-on-surface flex items-center gap-2">
          <FileText className="text-primary" size={20} />
          Research Library ({total})
        </h3>

        {/* Right-side controls */}
        <div className="flex items-center gap-2">
          {/* View Toggle Dropdown */}
          <div ref={viewDropdownRef} className="relative">
            <button
              type="button"
              onClick={() => setIsViewDropdownOpen((v) => !v)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high transition-colors text-sm font-medium cursor-pointer border-0"
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
              <div
                className="absolute right-0 top-full mt-2 z-[60] rounded-2xl shadow-xl p-1.5 min-w-[128px]"
                style={{ backgroundColor: "var(--color-surface-container-low, #f4f2ff)" }}
              >
                <button
                  type="button"
                  onClick={() => { setViewMode("grid"); setIsViewDropdownOpen(false); }}
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
                  onClick={() => { setViewMode("list"); setIsViewDropdownOpen(false); }}
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

          {/* Add Paper Button */}
          <button
            type="button"
            onClick={handleAddPaper}
            className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary text-on-primary font-semibold text-sm hover:opacity-90 transition-opacity shadow-sm cursor-pointer border-0"
          >
            <Plus size={15} />
            <span className="hidden sm:inline">Add Paper</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>
      </div>

      {/* Paper Cards */}
      <div className="text-left">
        {loading ? (
          <div className="flex justify-center p-12 rounded-3xl bg-surface-container-low/30">
            <Loader variant="spinner" diameter={36} strokeWidth={3} color="primary" message="Loading papers..." />
          </div>
        ) : loadError ? (
          <div className="p-12 text-center bg-surface-container-low/30 rounded-3xl text-on-surface-variant space-y-2">
            <p>Could not load research papers.</p>
            <p className="text-sm opacity-80">{loadError}</p>
          </div>
        ) : currentItems.length > 0 ? (
          viewMode === "grid" ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {currentItems.map((paper) => (
                <ResearchPaperCard key={paper.id} paper={paper} view="grid" />
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {currentItems.map((paper) => (
                <ResearchPaperCard key={paper.id} paper={paper} view="list" />
              ))}
            </div>
          )
        ) : (
          <div className="p-12 text-center bg-surface-container-low/30 rounded-3xl border border-dashed border-outline-variant/20 text-on-surface-variant">
            No papers match your search queries.
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 0 && totalPages > 1 && (
        <div className="flex justify-center mt-4 pt-4 border-t border-outline-variant/10">
          <ResearchPagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

    </div>
  );
}
