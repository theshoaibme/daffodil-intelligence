import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  type Node,
  BackgroundVariant,
  SelectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./flowTheme.css";

import type { Agent } from "@hooks";
import { useRuntimeStatus } from "@hooks";
import { subscribeFlow, type FlowState } from "@lib";
import { ActiveBeamEdge } from "./ActiveBeamEdge";
import { AgentHoverCard, type HoverAnchor } from "./AgentHoverCard";
import { FlowZoomControls } from "./FlowZoomControls";
import { flowNodeTypes } from "./FlowNodes";
import { FitViewOnUpdate } from "./FitViewOnUpdate";
import { buildAgentGraph } from "./graphBuilder";
import { loadLayout, saveLayout } from "./layoutStorage";
const edgeTypes = { activeBeam: ActiveBeamEdge };

const IDLE_OVERLAY = {
  activeAgentIds: [] as string[],
  activeInputId: "input-telegram",
  activeModelId: "gemini-2.0-flash",
  modelActive: false,
};

const HOVER_LEAVE_MS = 140;

interface AgentFlowCanvasProps {
  agents: Agent[];
  editing: boolean;
  onSave: () => void;
  saveSignal: number;
  /** When false, defer fit-to-view until the graph has finished loading. */
  graphReady?: boolean;
  /** Offset controls below a page header (agent hub flow view). */
  belowHeader?: boolean;
}

export function AgentFlowCanvas({
  agents,
  editing,
  onSave,
  saveSignal,
  graphReady = true,
  belowHeader = false,
}: AgentFlowCanvasProps) {
  const savedLayout = useMemo(() => loadLayout(agents), [agents]);
  const { runtime } = useRuntimeStatus();
  const [flow, setFlow] = useState<FlowState>({
    activeAgentIds: [],
    activeTools: [],
    modelActive: false,
  });

  useEffect(() => subscribeFlow(setFlow), []);
  const [fitTrigger, setFitTrigger] = useState(0);
  const [hoveredAgent, setHoveredAgent] = useState<Agent | null>(null);
  const [hoverAnchor, setHoverAnchor] = useState<HoverAnchor | null>(null);
  const [selectedCount, setSelectedCount] = useState(0);
  const nodesRef = useRef<Node[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const hoverLeaveTimer = useRef<number | null>(null);
  const resizeTimer = useRef<number | null>(null);

  const live = flow.modelActive || flow.activeAgentIds.length > 0;
  const graph = useMemo(
    () =>
      buildAgentGraph(agents, savedLayout, {
        activeAgentIds: live ? flow.activeAgentIds : IDLE_OVERLAY.activeAgentIds,
        activeInputId: IDLE_OVERLAY.activeInputId,
        modelActive: live ? flow.modelActive : IDLE_OVERLAY.modelActive,
        activeModelId: runtime.model || IDLE_OVERLAY.activeModelId,
        engine: runtime.engine,
      }),
    [agents, savedLayout, runtime.engine, runtime.model, live, flow.activeAgentIds, flow.modelActive]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(graph.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(graph.edges);

  nodesRef.current = nodes;

  useEffect(() => {
    setNodes((current) => {
      const positionById = new Map(current.map((n) => [n.id, n.position]));
      const selectedById = new Map(current.map((n) => [n.id, n.selected]));
      return graph.nodes.map((n) => ({
        ...n,
        position: positionById.get(n.id) ?? n.position,
        selected: selectedById.get(n.id) ?? false,
        draggable: editing,
      }));
    });
    setEdges(graph.edges);
  }, [graph.nodes, graph.edges, editing, setNodes, setEdges]);

  useEffect(() => {
    if (saveSignal === 0) return;
    saveLayout(nodesRef.current);
    onSave();
  }, [saveSignal, onSave]);

  useEffect(() => {
    if (!graphReady) return;
    setFitTrigger((n) => n + 1);
  }, [graphReady, agents.length]);

  useEffect(() => {
    if (!graphReady) return;

    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver(() => {
      if (resizeTimer.current !== null) {
        window.clearTimeout(resizeTimer.current);
      }
      resizeTimer.current = window.setTimeout(() => {
        setFitTrigger((n) => n + 1);
      }, 120);
    });

    observer.observe(el);
    return () => {
      observer.disconnect();
      if (resizeTimer.current !== null) {
        window.clearTimeout(resizeTimer.current);
      }
    };
  }, [graphReady]);

  const clearHoverLeaveTimer = useCallback(() => {
    if (hoverLeaveTimer.current !== null) {
      window.clearTimeout(hoverLeaveTimer.current);
      hoverLeaveTimer.current = null;
    }
  }, []);

  const scheduleHoverClear = useCallback(() => {
    clearHoverLeaveTimer();
    hoverLeaveTimer.current = window.setTimeout(() => {
      setHoveredAgent(null);
      setHoverAnchor(null);
    }, HOVER_LEAVE_MS);
  }, [clearHoverLeaveTimer]);

  const showAgentHover = useCallback(
    (agent: Agent, clientX: number, clientY: number) => {
      clearHoverLeaveTimer();
      setHoveredAgent(agent);
      setHoverAnchor({ x: clientX, y: clientY });
    },
    [clearHoverLeaveTimer]
  );

  const onNodeDragStop = useCallback(() => {
    if (editing) saveLayout(nodesRef.current);
  }, [editing]);

  const onSelectionChange = useCallback(({ nodes: selectedNodes }: { nodes: Node[] }) => {
    const agentNodes = selectedNodes.filter((n) => n.type === "agent");
    setSelectedCount(agentNodes.length);
  }, []);

  const onNodeMouseEnter = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (editing || node.type !== "agent") return;
      const agent = agents.find((a) => a.id === node.id);
      if (!agent) return;
      showAgentHover(agent, event.clientX, event.clientY);
    },
    [agents, editing, showAgentHover]
  );

  const onNodeMouseMove = useCallback(
    (event: React.MouseEvent, node: Node) => {
      if (editing || node.type !== "agent" || hoveredAgent?.id !== node.id) return;
      setHoverAnchor({ x: event.clientX, y: event.clientY });
    },
    [editing, hoveredAgent?.id]
  );

  const onNodeMouseLeave = useCallback(() => {
    scheduleHoverClear();
  }, [scheduleHoverClear]);

  const onPaneClick = useCallback(() => {
    clearHoverLeaveTimer();
    setHoveredAgent(null);
    setHoverAnchor(null);
  }, [clearHoverLeaveTimer]);

  useEffect(() => () => clearHoverLeaveTimer(), [clearHoverLeaveTimer]);

  return (
    <div ref={containerRef} className="agent-flow-canvas w-full h-full relative min-h-0">
      {selectedCount > 1 && editing && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 px-3 py-1.5 rounded-full bg-surface-container-lowest/95 border border-outline-variant/40 shadow-md text-xs font-medium text-on-surface">
          {selectedCount} agents selected — Shift+click to add more
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onNodeMouseEnter={onNodeMouseEnter}
        onNodeMouseMove={onNodeMouseMove}
        onNodeMouseLeave={onNodeMouseLeave}
        onSelectionChange={onSelectionChange}
        onPaneClick={onPaneClick}
        nodeTypes={flowNodeTypes}
        edgeTypes={edgeTypes}
        nodesDraggable={editing}
        nodesConnectable={false}
        elementsSelectable
        selectionOnDrag={editing}
        selectionMode={SelectionMode.Partial}
        multiSelectionKeyCode="Shift"
        panOnDrag={editing ? [1, 2] : true}
        panOnScroll
        zoomOnScroll
        zoomOnPinch
        minZoom={0.25}
        maxZoom={1.75}
        proOptions={{ hideAttribution: true }}
        className={editing ? "cursor-default" : "cursor-grab active:cursor-grabbing"}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#c5c5d9" />
        <FlowZoomControls belowHeader={belowHeader} />
        {!editing && <FitViewOnUpdate trigger={fitTrigger} />}
      </ReactFlow>

      {!editing && (
        <AgentHoverCard
          agent={hoveredAgent}
          anchor={hoverAnchor}
          onPointerEnter={clearHoverLeaveTimer}
          onPointerLeave={scheduleHoverClear}
        />
      )}
    </div>
  );
}
