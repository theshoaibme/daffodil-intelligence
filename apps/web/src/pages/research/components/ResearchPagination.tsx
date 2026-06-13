import { ChevronLeft, ChevronRight } from "lucide-react";

interface ResearchPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  maxVisible?: number;
}

function getVisiblePages(currentPage: number, totalPages: number, maxVisible: number): number[] {
  if (totalPages <= maxVisible) {
    return Array.from({ length: totalPages }, (_, i) => i + 1);
  }

  let start = currentPage - Math.floor(maxVisible / 2);
  let end = start + maxVisible - 1;

  if (start < 1) {
    start = 1;
    end = maxVisible;
  }

  if (end > totalPages) {
    end = totalPages;
    start = totalPages - maxVisible + 1;
  }

  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}

export function ResearchPagination({
  currentPage,
  totalPages,
  onPageChange,
  maxVisible = 5,
}: ResearchPaginationProps) {
  if (totalPages <= 1) return null;

  const visiblePages = getVisiblePages(currentPage, totalPages, maxVisible);
  const arrowClass =
    "p-2 rounded-full border border-outline-variant/20 text-on-surface-variant hover:bg-surface-container-low disabled:opacity-40 disabled:hover:bg-transparent transition-colors cursor-pointer shrink-0 bg-transparent";

  return (
    <nav
      className="flex max-w-full items-center justify-center gap-2 overflow-hidden"
      aria-label="Pagination"
    >
      <button
        type="button"
        onClick={() => onPageChange(Math.max(currentPage - 1, 1))}
        disabled={currentPage === 1}
        className={arrowClass}
        aria-label="Previous page"
      >
        <ChevronLeft size={16} />
      </button>

      <div className="flex shrink-0 items-center gap-1.5">
        {visiblePages.map((page) => (
          <button
            key={page}
            type="button"
            onClick={() => onPageChange(page)}
            aria-label={`Page ${page}`}
            aria-current={currentPage === page ? "page" : undefined}
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-all cursor-pointer ${
              currentPage === page
                ? "bg-primary text-on-primary shadow-sm border-0"
                : "border border-outline-variant/10 hover:bg-surface-container-low text-on-surface-variant bg-transparent"
            }`}
          >
            {page}
          </button>
        ))}
      </div>

      <button
        type="button"
        onClick={() => onPageChange(Math.min(currentPage + 1, totalPages))}
        disabled={currentPage === totalPages}
        className={arrowClass}
        aria-label="Next page"
      >
        <ChevronRight size={16} />
      </button>
    </nav>
  );
}
