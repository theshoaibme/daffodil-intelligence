import { ChevronLeft, ChevronRight } from "lucide-react";

interface ResearchPaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function ResearchPagination({ currentPage, totalPages, onPageChange }: ResearchPaginationProps) {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => onPageChange(Math.max(currentPage - 1, 1))}
        disabled={currentPage === 1}
        className="p-2 rounded-full border border-outline-variant/20 text-on-surface-variant hover:bg-surface-container-low disabled:opacity-40 disabled:hover:bg-transparent transition-colors cursor-pointer"
        aria-label="Previous page"
      >
        <ChevronLeft size={16} />
      </button>
      
      <div className="flex items-center gap-1.5">
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`w-9 h-9 rounded-full text-xs font-semibold flex items-center justify-center transition-all cursor-pointer ${
              currentPage === page
                ? "bg-primary text-on-primary shadow-sm"
                : "border border-outline-variant/10 hover:bg-surface-container-low text-on-surface-variant"
            }`}
          >
            {page}
          </button>
        ))}
      </div>

      <button
        onClick={() => onPageChange(Math.min(currentPage + 1, totalPages))}
        disabled={currentPage === totalPages}
        className="p-2 rounded-full border border-outline-variant/20 text-on-surface-variant hover:bg-surface-container-low disabled:opacity-40 disabled:hover:bg-transparent transition-colors cursor-pointer"
        aria-label="Next page"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
