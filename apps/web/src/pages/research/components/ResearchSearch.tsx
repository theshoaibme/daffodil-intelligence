import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { FileText, Plus, LayoutGrid, List, ChevronDown } from "lucide-react";
import { ResearchPaper } from "./types";
import { ResearchPaperCard } from "./ResearchPaperCard";
import { AddPaperModal } from "./AddPaperModal";
import { ResearchDropdown } from "./ResearchDropdown";
import { ResearchPagination } from "./ResearchPagination";
import { PlaceholdersAndVanishInput } from "@ui";
import { getPapers, addPaper, generateId, CATEGORIES } from "./paperStore";

type ViewMode = "grid" | "list";

export function ResearchSearch() {
  const [searchParams] = useSearchParams();
  const initialCategory = searchParams.get("category") || "All";
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState(
    CATEGORIES.includes(initialCategory) ? initialCategory : "All"
  );
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [isViewDropdownOpen, setIsViewDropdownOpen] = useState(false);
  const [papers, setPapers] = useState<ResearchPaper[]>(getPapers);

  const searchRef = useRef<HTMLDivElement>(null);
  const viewDropdownRef = useRef<HTMLDivElement>(null);

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

  const filteredPapers = papers.filter((item) => {
    const matchesSearch =
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.authors.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.abstract.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // Reset page to 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory]);

  // Pagination Settings
  const itemsPerPage = 16;
  const totalPages = Math.ceil(filteredPapers.length / itemsPerPage);
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredPapers.slice(indexOfFirstItem, indexOfLastItem);

  const handleAddPaper = (newPaperData: Omit<ResearchPaper, "citations" | "id">) => {
    const newPaper: ResearchPaper = {
      ...newPaperData,
      id: generateId(newPaperData.title),
      citations: 0,
    };
    addPaper(newPaper);
    setPapers(getPapers());
  };

  const handleSelectSearch = (term: string) => {
    setSearchQuery(term);
    setIsDropdownOpen(false);
  };

  // Only show categories that have papers
  const activeCategories = CATEGORIES.filter(
    (cat) => cat === "All" || papers.some((p) => p.category === cat)
  );

  return (
    <div className="space-y-6 sm:space-y-8 relative">
      {/* Centered Search & Category Filter Section */}
      <div className="flex flex-col items-center gap-4 text-center relative z-20 max-w-2xl mx-auto">
        <div ref={searchRef} className="relative w-full">
          <PlaceholdersAndVanishInput
            placeholders={[
              "Search papers by title, author, abstract...",
              "e.g. Attention Is All You Need",
              "e.g. Protein structure prediction with AlphaFold",
              "e.g. Quantum Cryptography in Smart Grids",
              "e.g. Vision Transformers for image recognition",
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
          Research Library ({filteredPapers.length})
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
            onClick={() => setIsAddModalOpen(true)}
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
        {currentItems.length > 0 ? (
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
      {filteredPapers.length > 0 && totalPages > 1 && (
        <div className="flex justify-center mt-4 pt-4 border-t border-outline-variant/10">
          <ResearchPagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

      {/* Add Research Paper Modal */}
      <AddPaperModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAdd={handleAddPaper}
      />
    </div>
  );
}
