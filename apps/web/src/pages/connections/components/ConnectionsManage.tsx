import { useMemo, useState } from "react";
import { Building2, GraduationCap, MessageSquare, Search, Users } from "lucide-react";

type ConnectionType = "university" | "professor";

interface AcademicConnection {
  id: string;
  type: ConnectionType;
  name: string;
  subtitle: string;
  focus: string;
  location?: string;
  members?: number;
  status: "connected" | "available";
}

const CONNECTIONS: AcademicConnection[] = [
  {
    id: "mit",
    type: "university",
    name: "Massachusetts Institute of Technology",
    subtitle: "MIT · Cambridge, USA",
    focus: "Artificial Intelligence & Computer Science",
    location: "Cambridge, USA",
    members: 48,
    status: "connected",
  },
  {
    id: "stanford",
    type: "university",
    name: "Stanford University",
    subtitle: "Stanford · California, USA",
    focus: "Machine Learning & Human-Centered AI",
    location: "Stanford, USA",
    members: 36,
    status: "connected",
  },
  {
    id: "oxford",
    type: "university",
    name: "University of Oxford",
    subtitle: "Oxford · United Kingdom",
    focus: "Quantum Computing & Ethics",
    location: "Oxford, UK",
    members: 29,
    status: "available",
  },
  {
    id: "daffodil",
    type: "university",
    name: "Daffodil International University",
    subtitle: "Daffodil · Dhaka, Bangladesh",
    focus: "AI in Education & Smart Systems",
    location: "Dhaka, Bangladesh",
    members: 22,
    status: "connected",
  },
  {
    id: "prof-vaswani",
    type: "professor",
    name: "Prof. Ashish Vaswani",
    subtitle: "Former Google Brain · NLP Research",
    focus: "Transformers & Sequence Modeling",
    status: "available",
  },
  {
    id: "prof-lecun",
    type: "professor",
    name: "Prof. Yann LeCun",
    subtitle: "Meta AI · NYU",
    focus: "Deep Learning & Computer Vision",
    status: "available",
  },
  {
    id: "prof-hinton",
    type: "professor",
    name: "Prof. Geoffrey Hinton",
    subtitle: "University of Toronto",
    focus: "Neural Networks & AI Safety",
    status: "connected",
  },
  {
    id: "prof-ng",
    type: "professor",
    name: "Prof. Andrew Ng",
    subtitle: "Stanford · DeepLearning.AI",
    focus: "Machine Learning Education",
    status: "connected",
  },
  {
    id: "prof-fei-fei",
    type: "professor",
    name: "Prof. Fei-Fei Li",
    subtitle: "Stanford HAI",
    focus: "Computer Vision & AI Policy",
    status: "available",
  },
];

type FilterType = "all" | ConnectionType;

function ConnectionCard({ item }: { item: AcademicConnection }) {
  const Icon = item.type === "university" ? Building2 : GraduationCap;

  return (
    <article className="p-5 flex flex-col justify-between bg-surface-container-low rounded-2xl transition-all duration-200 hover:bg-surface-container min-h-[220px]">
      <div className="space-y-3 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <span
            className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${
              item.type === "university"
                ? "text-primary bg-primary/10"
                : "text-secondary bg-secondary/10"
            }`}
          >
            {item.type === "university" ? "University" : "Professor"}
          </span>
          <span
            className={`text-[10px] font-semibold px-2.5 py-1 rounded-full ${
              item.status === "connected"
                ? "bg-emerald-500/10 text-emerald-600"
                : "bg-surface-container-high text-on-surface-variant"
            }`}
          >
            {item.status === "connected" ? "Connected" : "Available"}
          </span>
        </div>

        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-surface-container-lowest shrink-0">
            <Icon size={18} className="text-primary" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-base text-on-surface line-clamp-2 leading-snug">
              {item.name}
            </h3>
            <p className="text-xs text-on-surface-variant/80 mt-1">{item.subtitle}</p>
          </div>
        </div>

        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-2">
          {item.focus}
        </p>
      </div>

      <div className="flex items-center justify-between mt-4 pt-3 border-t border-outline-variant/10">
        {item.members ? (
          <span className="text-[11px] text-on-surface-variant/70 flex items-center gap-1">
            <Users size={13} className="text-primary/70" />
            {item.members} faculty linked
          </span>
        ) : (
          <span className="text-[11px] text-on-surface-variant/70">Direct messaging</span>
        )}
        <button
          type="button"
          className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-primary hover:underline cursor-pointer border-0 bg-transparent"
        >
          <MessageSquare size={13} />
          {item.status === "connected" ? "Message" : "Connect"}
        </button>
      </div>
    </article>
  );
}

export function ConnectionsManage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");

  const filtered = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return CONNECTIONS.filter((item) => {
      const matchesType = filter === "all" || item.type === filter;
      const matchesSearch =
        !q ||
        item.name.toLowerCase().includes(q) ||
        item.subtitle.toLowerCase().includes(q) ||
        item.focus.toLowerCase().includes(q) ||
        (item.location?.toLowerCase().includes(q) ?? false);
      return matchesType && matchesSearch;
    });
  }, [searchQuery, filter]);

  const universityCount = CONNECTIONS.filter((c) => c.type === "university").length;
  const professorCount = CONNECTIONS.filter((c) => c.type === "professor").length;
  const connectedCount = CONNECTIONS.filter((c) => c.status === "connected").length;

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="space-y-2">
        <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-on-surface">
          Intercommunication system
        </h2>
        <p className="text-sm text-on-surface-variant max-w-3xl leading-relaxed">
          Connect with top professors, universities, and research networks. Share knowledge,
          coordinate collaborations, and bridge academic communities through one workspace.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Universities", value: universityCount, icon: Building2 },
          { label: "Professors", value: professorCount, icon: GraduationCap },
          { label: "Active links", value: connectedCount, icon: MessageSquare },
        ].map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="rounded-2xl bg-surface-container-low px-5 py-4 flex items-center gap-3"
          >
            <div className="p-2 rounded-xl bg-primary/10 text-primary">
              <Icon size={18} />
            </div>
            <div>
              <p className="text-xs text-on-surface-variant">{label}</p>
              <p className="text-xl font-semibold text-on-surface tabular-nums">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h3 className="text-lg font-semibold text-on-surface">
            Network ({filtered.length})
          </h3>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
            <div className="flex gap-1.5">
              {(
                [
                  { id: "all", label: "All" },
                  { id: "university", label: "Universities" },
                  { id: "professor", label: "Professors" },
                ] as const
              ).map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setFilter(id)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer border-0 ${
                    filter === id
                      ? "bg-primary text-on-primary"
                      : "bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="relative w-full sm:max-w-xs">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60"
              />
              <input
                type="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search universities or professors..."
                className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-surface-container-lowest text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm border-0"
              />
            </div>
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="p-10 text-center rounded-3xl bg-surface-container-low/50 text-on-surface-variant">
            No connections match your search.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((item) => (
              <ConnectionCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
