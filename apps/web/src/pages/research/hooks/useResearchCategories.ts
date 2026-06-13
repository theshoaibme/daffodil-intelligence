import { useCallback, useEffect, useState } from "react";
import { CATEGORY_OTHERS, researchApi } from "@lib/researchApi";

const DEFAULT_CATEGORIES = [
  "Computer Science",
  "AI & Education",
  "Machine Learning",
  "Natural Language Processing",
  "Computer Vision",
  "Smart Grids",
  "Cybersecurity",
  "Bioinformatics",
  "Quantum Computing",
  "Robotics",
  "Data Science",
];

export function useResearchCategories() {
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [formCategories, setFormCategories] = useState<string[]>([
    ...DEFAULT_CATEGORIES,
    CATEGORY_OTHERS,
  ]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const res = await researchApi.listCategories();
      if (res.categories.length > 0) setCategories(res.categories);
      if (res.form_categories.length > 0) setFormCategories(res.form_categories);
    } catch {
      // keep defaults when API unavailable
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const filterCategories = ["All", ...categories];

  return { categories, formCategories, filterCategories, loading, refresh };
}
