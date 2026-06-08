import React, { useCallback, useLayoutEffect, useRef, useState } from "react";
import { useAgents } from "../../../hooks/useAgents";
import { Bot, Zap, Brain, Monitor, Cpu, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";

const ROOT_AGENT = {
  id: "daffodil-intelligence",
  name: "Daffodil Intelligence",
  category: "orchestration",
  status: "idle" as const,
};

const MIN_ZOOM = 0.35;
const MAX_ZOOM = 1.75;
const ZOOM_STEP = 0.12;

const categoryColors: Record<string, string> = {
  university: "text-secondary bg-secondary-container/50 border-secondary/30",
  computer: "text-primary bg-primary/10 border-primary/30",
  orchestration: "text-tertiary bg-tertiary/10 border-tertiary/30",
  productivity: "text-green-600 bg-green-50 border-green-200",
  ai: "text-purple-600 bg-purple-50 border-purple-200",
  general: "text-on-surface-variant bg-surface-container border-outline-variant",
};

const categoryIcons: Record<string, React.ElementType> = {
  university: Bot,
  computer: Monitor,
  orchestration: Brain,
  productivity: Zap,
  ai: Cpu,
  general: Bot,
};

const statusDots: Record<string, string> = {
  idle: "bg-outline-variant",
  thinking: "bg-primary animate-pulse",
  executing: "bg-tertiary animate-pulse",
  error: "bg-error",
};

function AgentNode({
  agent,
  isRoot = false,
  nodeRef,
}: {
  agent: { id: string; name: string; category?: string; status?: string };
  isRoot?: boolean;
  nodeRef?: React.Ref<HTMLDivElement>;
}) {
  const category = agent.category || "general";
  const catColor = isRoot
    ? "text-primary bg-primary/20 border-primary shadow-lg"
    : categoryColors[category] || categoryColors.general;
  const Icon = isRoot ? Brain : categoryIcons[category] || Bot;

  return (
    <div
      ref={nodeRef}
      className={`relative z-10 flex flex-col items-center justify-center p-3 w-44 rounded-2xl border-2 bg-surface-container-lowest shadow-sm hover:shadow-md transition-shadow cursor-default select-none ${
        isRoot
          ? "border-primary min-h-[120px]"
          : "border-outline-variant hover:border-primary/50"
      }`}
    >
      <div
        className={`rounded-full flex items-center justify-center mb-2 ${catColor} ${
          isRoot ? "w-16 h-16" : "w-12 h-12"
        }`}
      >
        <Icon size={isRoot ? 32 : 24} />
      </div>
      <h3 className="text-sm font-semibold text-on-surface text-center leading-snug line-clamp-2 px-1">
        {agent.name}
      </h3>
      {!isRoot && (
        <span
          className={`mt-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full capitalize ${categoryColors[category]}`}
        >
          {category}
        </span>
      )}
      {!isRoot && agent.status && (
        <div className="absolute -top-1 -right-1 flex items-center bg-surface-container-lowest border border-outline-variant rounded-full px-1.5 py-0.5 shadow-sm">
          <div className={`w-2 h-2 rounded-full ${statusDots[agent.status] || statusDots.idle}`} />
        </div>
      )}
    </div>
  );
}

function CategoryNode({
  category,
  nodeRef,
}: {
  category: string;
  nodeRef?: React.Ref<HTMLDivElement>;
}) {
  const catColor = categoryColors[category] || categoryColors.general;
  const Icon = categoryIcons[category] || Bot;

  return (
    <div
      ref={nodeRef}
      className={`relative z-10 flex items-center gap-2 px-4 py-2 rounded-xl border-2 bg-surface-container-lowest shadow-sm ${catColor}`}
    >
      <Icon size={16} />
      <span className="text-xs font-bold uppercase tracking-wider">{category}</span>
    </div>
  );
}

export default function AgentDashboard() {
  const { agents, loading, error, refetch } = useAgents();

  const viewportRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLDivElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const categoryRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const agentRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const [zoom, setZoom] = useState(0.85);
  const [pan, setPan] = useState({ x: 48, y: 48 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0, panX: 0, panY: 0 });
  const [connections, setConnections] = useState<
    { x1: number; y1: number; x2: number; y2: number; active: boolean }[]
  >([]);

  const grouped = agents.reduce(
    (acc, agent) => {
      const cat = agent.category || "general";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(agent);
      return acc;
    },
    {} as Record<string, typeof agents>
  );

  const categoryOrder = ["orchestration", "computer", "productivity", "university", "ai", "general"];
  const sortedCategories = [
    ...categoryOrder.filter((c) => grouped[c]?.length),
    ...Object.keys(grouped).filter((c) => !categoryOrder.includes(c)),
  ];

  const clampZoom = (z: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));

  const updateConnections = useCallback(() => {
    if (!canvasRef.current || !rootRef.current) return;

    const canvasRect = canvasRef.current.getBoundingClientRect();
    const getCenter = (el: HTMLElement) => {
      const rect = el.getBoundingClientRect();
      return {
        x: rect.left - canvasRect.left + rect.width / 2,
        y: rect.top - canvasRect.top + rect.height / 2,
      };
    };

    const newConnections: typeof connections = [];
    const rootCenter = getCenter(rootRef.current);

    sortedCategories.forEach((cat) => {
      const catEl = categoryRefs.current[cat];
      if (!catEl) return;

      const catCenter = getCenter(catEl);
      newConnections.push({
        x1: rootCenter.x,
        y1: rootCenter.y,
        x2: catCenter.x,
        y2: catCenter.y,
        active: false,
      });

      grouped[cat].forEach((agent) => {
        const agentEl = agentRefs.current[agent.id];
        if (!agentEl) return;
        const agentCenter = getCenter(agentEl);
        newConnections.push({
          x1: catCenter.x,
          y1: catCenter.y,
          x2: agentCenter.x,
          y2: agentCenter.y,
          active: agent.status !== "idle",
        });
      });
    });

    setConnections(newConnections);
  }, [agents, sortedCategories, grouped]);

  useLayoutEffect(() => {
    const timer = setTimeout(updateConnections, 80);
    window.addEventListener("resize", updateConnections);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", updateConnections);
    };
  }, [updateConnections, zoom, pan]);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 1 - ZOOM_STEP : 1 + ZOOM_STEP;
    setZoom((z) => clampZoom(z * delta));
  }, []);

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (e.button !== 0 && e.button !== 1) return;
      const target = e.target as HTMLElement;
      if (target.closest("[data-agent-node]")) return;
      setIsPanning(true);
      panStart.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y };
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    },
    [pan]
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!isPanning) return;
      setPan({
        x: panStart.current.panX + (e.clientX - panStart.current.x),
        y: panStart.current.panY + (e.clientY - panStart.current.y),
      });
    },
    [isPanning]
  );

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    setIsPanning(false);
    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
  }, []);

  const fitView = useCallback(() => {
    setZoom(0.85);
    setPan({ x: 48, y: 48 });
  }, []);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden relative">
      <div className="px-6 py-4 border-b border-outline-variant bg-surface-container-low flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Brain size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-on-surface">Agents</h1>
            <p className="text-xs text-on-surface-variant">Workflow canvas · drag to pan · scroll to zoom</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-medium text-on-surface-variant bg-surface-container px-3 py-1.5 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span>{agents.filter((a) => a.status !== "idle").length} active</span>
          </div>
          <button
            type="button"
            onClick={refetch}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-on-surface-variant hover:bg-surface-container-high transition-colors"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      <div
        ref={viewportRef}
        className={`flex-1 relative overflow-hidden ${isPanning ? "cursor-grabbing" : "cursor-grab"}`}
        style={{
          backgroundColor: "#f4f2ff",
          backgroundImage: "radial-gradient(#c5c5d9 1px, transparent 1px)",
          backgroundSize: `${20 * zoom}px ${20 * zoom}px`,
          backgroundPosition: `${pan.x}px ${pan.y}px`,
        }}
        onWheel={handleWheel}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      >
        <div
          ref={canvasRef}
          className="absolute top-0 left-0 origin-top-left will-change-transform"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          }}
        >
          <svg className="absolute top-0 left-0 w-[4000px] h-[2400px] pointer-events-none z-0">
            <defs>
              <linearGradient id="active-beam" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4259ff" stopOpacity="0.85" />
                <stop offset="100%" stopColor="#c04500" stopOpacity="0.85" />
              </linearGradient>
            </defs>
            {connections.map((conn, i) => (
              <path
                key={i}
                d={`M ${conn.x1} ${conn.y1} C ${conn.x1} ${(conn.y1 + conn.y2) / 2}, ${conn.x2} ${(conn.y1 + conn.y2) / 2}, ${conn.x2} ${conn.y2}`}
                fill="none"
                stroke={conn.active ? "url(#active-beam)" : "#c5c5d9"}
                strokeWidth={conn.active ? 2.5 : 1.75}
                className={conn.active ? "animate-pulse" : ""}
              />
            ))}
          </svg>

          <div className="relative z-10 flex flex-col items-center gap-20 pt-16 pb-32 px-24 min-w-[1200px]">
            <div data-agent-node className="flex justify-center">
              <AgentNode agent={ROOT_AGENT} isRoot nodeRef={rootRef} />
            </div>

            <div className="flex justify-center gap-16 lg:gap-24 flex-wrap">
              {sortedCategories.map((cat) => (
                <div key={cat} className="flex flex-col items-center gap-14">
                  <CategoryNode category={cat} nodeRef={(el) => (categoryRefs.current[cat] = el)} />

                  <div className="flex gap-5 flex-wrap justify-center max-w-[420px]">
                    {grouped[cat].map((agent) => (
                      <div key={agent.id} data-agent-node>
                        <AgentNode
                          agent={agent}
                          nodeRef={(el) => (agentRefs.current[agent.id] = el)}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="absolute bottom-6 left-6 z-30 flex items-center gap-1 bg-surface-container-lowest border border-outline-variant rounded-xl shadow-md p-1">
          <button
            type="button"
            onClick={() => setZoom((z) => clampZoom(z - ZOOM_STEP))}
            className="p-2 rounded-lg hover:bg-surface-container-high text-on-surface-variant"
            aria-label="Zoom out"
          >
            <ZoomOut size={18} />
          </button>
          <span className="text-xs font-medium text-on-surface min-w-[3rem] text-center tabular-nums">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            onClick={() => setZoom((z) => clampZoom(z + ZOOM_STEP))}
            className="p-2 rounded-lg hover:bg-surface-container-high text-on-surface-variant"
            aria-label="Zoom in"
          >
            <ZoomIn size={18} />
          </button>
          <button
            type="button"
            onClick={fitView}
            className="p-2 rounded-lg hover:bg-surface-container-high text-on-surface-variant border-l border-outline-variant ml-0.5 pl-2.5"
            aria-label="Reset view"
          >
            <Maximize2 size={18} />
          </button>
        </div>

        {loading && agents.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 z-50">
            <RefreshCw size={32} className="animate-spin text-primary mb-4" />
            <p className="text-on-surface-variant font-medium">Loading agents…</p>
          </div>
        )}

        {error && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-error-container text-on-error-container px-4 py-2 rounded-xl text-sm z-50 shadow-lg">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
