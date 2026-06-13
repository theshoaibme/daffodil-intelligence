/** @deprecated Use researchApi and useResearchCategories instead. */
export { CATEGORY_OTHERS } from "@lib/researchApi";

export function generateId(title: string): string {
  return (
    title
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, "")
      .trim()
      .replace(/\s+/g, "-")
      .slice(0, 40) +
    "-" +
    Date.now().toString(36)
  );
}
