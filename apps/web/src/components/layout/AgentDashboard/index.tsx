import React, { useCallback, useRef, useState, useLayoutEffect } from "react";
import { useAgents } from "../../../hooks/useAgents";
import { Bot, Zap, Brain, Monitor, Cpu, RefreshCw, Circle, User } from "lucide-react";

const categoryColors: Record<string, string> = {
  university: "text-secondary bg-secondary-container/50 border-secondary/30",
  computer: "text-primary bg-primary/10 border-primary/30",
  orchestration: "text-tertiary bg-tertiary/10 border-tertiary/30",
  productivity: "text-green-600 bg-green-50 border-green-200",
  ai: "text-purple-600 bg-purple-50 border-purple-200",
};

const categoryIcons: Record<string, React.ElementType> = {
  university: Bot,
  computer: Monitor,
  orchestration: Brain,
  productivity: Zap,
  ai: Cpu,
};

const statusColors: Record<string, string> = {
  idle: "bg-surface-dim text-on-surface-variant",
  thinking: "bg-primary/10 text-primary animate-pulse",
  executing: "bg-tertiary/10 text-tertiary animate-pulse",
  error: "bg-error-container text-on-error-container",
};

const statusDots: Record<string, string> = {
  idle: "bg-outline-variant",
  thinking: "bg-primary animate-pulse",
  executing: "bg-tertiary animate-pulse",
  error: "bg-error",
};

function AgentNode({ agent, isRoot = false, nodeRef }: { agent: any, isRoot?: boolean, nodeRef?: React.Ref<HTMLDivElement> }) {
  const catColor = isRoot ? "text-primary bg-primary/20 border-primary shadow-lg" : categoryColors[agent.category] || categoryColors.university;
  const Icon = categoryIcons[agent.category] || Bot;

  return (
    <div 
      ref={nodeRef}
      className={`relative z-10 flex flex-col items-center justify-center p-3 w-40 rounded-2xl border-2 bg-surface-container-lowest shadow-sm hover:shadow-md transition-all cursor-pointer ${isRoot ? 'border-primary scale-110' : 'border-outline-variant hover:border-primary/50'}`}
    >
      <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 ${catColor} ${isRoot ? 'w-16 h-16' : ''}`}>
        {isRoot ? <Brain size={isRoot ? 32 : 24} /> : <Icon size={24} />}
      </div>
      <h3 className="text-sm font-bold text-on-surface text-center leading-tight line-clamp-2">{agent.name}</h3>
      {!isRoot && (
        <span className={`mt-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${categoryColors[agent.category]} capitalize`}>
          {agent.category}
        </span>
      )}
      
      {/* Status indicator */}
      {!isRoot && (
        <div className="absolute -top-1 -right-1 flex items-center gap-1.5 bg-surface-container-lowest border border-outline-variant rounded-full px-1.5 py-0.5 shadow-sm">
          <div className={`w-2 h-2 rounded-full ${statusDots[agent.status]}`} />
        </div>
      )}
    </div>
  );
}

function CategoryNode({ category, nodeRef }: { category: string, nodeRef?: React.Ref<HTMLDivElement> }) {
  const catColor = categoryColors[category] || categoryColors.university;
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
  
  const containerRef = useRef<HTMLDivElement>(null);
  const [connections, setConnections] = useState<{x1: number, y1: number, x2: number, y2: number, active: boolean}[]>([]);
  
  // Refs for calculating line positions
  const rootRef = useRef<HTMLDivElement>(null);
  const categoryRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const agentRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const grouped = agents.reduce((acc, agent) => {
    // Skip planning agent from categories if we treat it as root or special
    if (agent.id === 'planning') return acc;
    
    const cat = agent.category || "general";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(agent);
    return acc;
  }, {} as Record<string, typeof agents>);

  const categoryOrder = ["computer", "productivity", "university", "ai"];
  const sortedCategories = [
    ...categoryOrder.filter((c) => grouped[c]),
    ...Object.keys(grouped).filter((c) => !categoryOrder.includes(c)),
  ];

  const rootAgent = agents.find(a => a.id === 'planning') || { 
    id: 'root', 
    name: 'Master Orchestrator', 
    category: 'orchestration',
    status: 'idle'
  };

  const updateConnections = useCallback(() => {
    if (!containerRef.current || !rootRef.current) return;
    
    const containerRect = containerRef.current.getBoundingClientRect();
    const getCenter = (el: HTMLElement) => {
      const rect = el.getBoundingClientRect();
      return {
        x: rect.left - containerRect.left + rect.width / 2,
        y: rect.top - containerRect.top + rect.height / 2
      };
    };

    const newConnections: typeof connections = [];
    const rootCenter = getCenter(rootRef.current);

    // Connect Root to Categories
    sortedCategories.forEach(cat => {
      const catEl = categoryRefs.current[cat];
      if (catEl) {
        const catCenter = getCenter(catEl);
        newConnections.push({
          x1: rootCenter.x, y1: rootCenter.y,
          x2: catCenter.x, y2: catCenter.y,
          active: false
        });

        // Connect Category to its Agents
        grouped[cat].forEach(agent => {
          const agentEl = agentRefs.current[agent.id];
          if (agentEl) {
            const agentCenter = getCenter(agentEl);
            newConnections.push({
              x1: catCenter.x, y1: catCenter.y,
              x2: agentCenter.x, y2: agentCenter.y,
              active: agent.status !== 'idle'
            });
          }
        });
      }
    });

    setConnections(newConnections);
  }, [agents, sortedCategories, grouped]);

  // Update connections on render and window resize
  useLayoutEffect(() => {
    // Use timeout to wait for actual DOM layout
    const timer = setTimeout(updateConnections, 100);
    window.addEventListener('resize', updateConnections);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updateConnections);
    };
  }, [updateConnections]);

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden relative">
      {/* Header */}
      <div className="px-6 py-4 border-b border-outline-variant bg-surface-container-low flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <Brain size={20} className="text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-on-surface">Agents</h1>
            <p className="text-xs text-on-surface-variant">
              System Architecture & Node Topology
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-medium text-on-surface-variant bg-surface-container px-3 py-1.5 rounded-lg">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            <span>{agents.filter(a => a.status !== 'idle').length} Active</span>
          </div>
          <button
            onClick={refetch}
            className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-on-surface-variant hover:bg-surface-container-high transition-colors"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Main Canvas */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto p-12 custom-scrollbar relative"
      >
        {/* SVG Connections Overlay */}
        <svg className="absolute top-0 left-0 w-full h-full pointer-events-none z-0 min-w-max min-h-max">
          <defs>
            <linearGradient id="active-beam" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4259ff" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#c04500" stopOpacity="0.8" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          {connections.map((conn, i) => (
            <path
              key={i}
              d={`M ${conn.x1} ${conn.y1} C ${conn.x1} ${(conn.y1 + conn.y2)/2}, ${conn.x2} ${(conn.y1 + conn.y2)/2}, ${conn.x2} ${conn.y2}`}
              fill="none"
              stroke={conn.active ? "url(#active-beam)" : "#c5c5d9"}
              strokeWidth={conn.active ? 3 : 2}
              className={conn.active ? "animate-pulse" : ""}
              filter={conn.active ? "url(#glow)" : ""}
              strokeDasharray={conn.active ? "8,4" : "none"}
            />
          ))}
        </svg>

        {/* Nodes Structure */}
        <div className="flex flex-col items-center gap-16 min-w-max pb-20">
          
          {/* Level 0: Root */}
          <div className="flex justify-center">
            <AgentNode agent={rootAgent} isRoot={true} nodeRef={rootRef} />
          </div>

          {/* Categories and their agents */}
          <div className="flex justify-center gap-12 lg:gap-20">
            {sortedCategories.map(cat => (
              <div key={cat} className="flex flex-col items-center gap-12">
                {/* Level 1: Category */}
                <CategoryNode 
                  category={cat} 
                  nodeRef={el => categoryRefs.current[cat] = el} 
                />

                {/* Level 2: Agents under Category */}
                <div className="flex gap-6 flex-wrap justify-center max-w-[400px]">
                  {grouped[cat].map(agent => (
                    <AgentNode 
                      key={agent.id} 
                      agent={agent} 
                      nodeRef={el => agentRefs.current[agent.id] = el} 
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>

        </div>

        {/* Loading overlay if totally empty */}
        {loading && agents.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/80 z-50">
            <RefreshCw size={32} className="animate-spin text-primary mb-4" />
            <p className="text-on-surface-variant font-medium">Initializing AI Operating System...</p>
          </div>
        )}

        {error && (
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-error-container text-on-error-container px-4 py-2 rounded-xl text-sm z-50 shadow-lg">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}
