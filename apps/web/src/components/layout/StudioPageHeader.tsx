import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { ROUTES } from "@lib";
import { cn } from "@lib/utils";

export function StudioPageHeader({
  title,
  borderless = false,
}: {
  title: string;
  borderless?: boolean;
}) {
  return (
    <header
      className={cn(
        "sticky top-0 z-20 w-full bg-background/90 backdrop-blur-md",
        !borderless && "border-b border-outline-variant/30",
      )}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center gap-3">
        <Link
          to={ROUTES.home}
          className="p-2 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors shrink-0"
          aria-label="Back to studio"
        >
          <ArrowLeft size={20} />
        </Link>
        <span className="font-medium text-base sm:text-lg truncate">{title}</span>
      </div>
    </header>
  );
}
