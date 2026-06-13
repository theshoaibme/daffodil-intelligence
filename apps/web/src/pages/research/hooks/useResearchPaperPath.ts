import { useLocation } from "react-router-dom";
import { isStudioPath, researchPaperPath } from "@lib";

export function useResearchPaperPath(paperId: string): string {
  const location = useLocation();
  const workspace = isStudioPath(location.pathname);
  return researchPaperPath(paperId, { workspace });
}
