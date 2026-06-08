import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Sparkles } from "lucide-react";
import { ROUTES } from "../../lib/routes";
import { getAuthHeaders } from "../../lib/api";

const API_BASE = import.meta.env.VITE_API_URL || "";

interface SkillItem {
  id: string;
  name: string;
  description: string;
  tags?: string[];
  is_public?: boolean;
}

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(`${API_BASE}/api/skills/hub`, { headers: getAuthHeaders() });
        if (!res.ok) throw new Error("Failed to load skills");
        const data = await res.json();
        if (!cancelled) {
          setSkills(data.skills ?? []);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load skills");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-background text-on-surface font-sans">
      <header className="border-b border-outline-variant/40 bg-surface-container-lowest/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-3">
          <Link
            to={ROUTES.home}
            className="p-2 rounded-full text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors"
            aria-label="Back to chat"
          >
            <ArrowLeft size={20} />
          </Link>
          <span className="font-medium text-lg">Skills</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
        <div className="flex items-start gap-4 mb-8">
          <div className="p-3 rounded-2xl bg-primary/10 text-primary">
            <Sparkles size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-medium tracking-tight mb-1">Skill library</h1>
            <p className="text-sm text-on-surface-variant">
              Reusable capabilities and instructions assigned to agents.
            </p>
          </div>
        </div>

        {loading && <p className="text-sm text-on-surface-variant">Loading skills…</p>}
        {error && <p className="text-sm text-error">{error}</p>}

        {!loading && !error && skills.length === 0 && (
          <p className="text-sm text-on-surface-variant">No skills configured yet.</p>
        )}

        <ul className="grid gap-3 sm:grid-cols-2">
          {skills.map((skill) => (
            <li
              key={skill.id}
              className="rounded-2xl border border-outline-variant/40 bg-surface-container-lowest p-4"
            >
              <p className="text-sm font-semibold text-on-surface">{skill.name}</p>
              {skill.description && (
                <p className="text-xs text-on-surface-variant/80 mt-1 leading-relaxed">
                  {skill.description}
                </p>
              )}
              {skill.tags && skill.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {skill.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-primary/10 text-primary"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
