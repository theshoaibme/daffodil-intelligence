import { useNavigate } from "react-router-dom";
import { Sparkles, MessageSquare } from "lucide-react";
import { Button } from "@components/ui";
import { ROUTES } from "@lib";

export function ResearchFooter() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-6 relative overflow-hidden py-6">
      <div className="flex items-center gap-3 text-sm sm:text-base text-on-surface-variant text-left">
        <Sparkles size={18} className="text-primary animate-pulse shrink-0" />
        <span>Ready to start? Select "Research" mode.</span>
      </div>
      <Button
        variant="contained"
        onClick={() => navigate(`${ROUTES.home}?agents=1`)}
        className="w-full sm:w-auto px-8 py-3 text-sm sm:text-base font-semibold rounded-full"
      >
        <MessageSquare size={18} className="mr-2" />
        Start Session
      </Button>
    </div>
  );
}
