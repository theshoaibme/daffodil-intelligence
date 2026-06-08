import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { Agent } from "../../../hooks/useAgents";
import { ActiveBeamEdge } from "./ActiveBeamEdge";
import { flowNodeTypes } from "./FlowNodes";
import { buildAgentGraph } from "./graphBuilder";
import { loadLayout, saveLayout } from "./layoutStorage";

const edgeTypes = { activeBeam: ActiveBeamEdge };

interface AgentFlowCanvasProps {
  agents: Agent[];
  editing: boolean;
  onSave: () => void;
  saveSignal: number;
}

export function AgentFlowCanvas({ agents, editing, onSave, saveSignal }: AgentFlowCanvasProps) {
  const savedLayout = useMemo(() => loadLayout(), []);
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const simulationIndex = useRef(0);
  const nodesRef = useRef<Node[]>([]);

  const graph = useMemo(
    () => buildAgentGraph(agents, savedLayout, activeAgentId),
    [agents, savedLayout, activeAgentId]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(graph.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(graph.edges);

  nodesRef.current = nodes;

  useEffect(() => {
    setNodes((current) => {
      const positionById = new Map(current.map((n) => [n.id, n.position]));
      return graph.nodes.map((n) => ({
        ...n,
        position: positionById.get(n.id) ?? n.position,
        draggable: editing,
      }));
    });
    setEdges(graph.edges);
  }, [graph.nodes, graph.edges, editing, setNodes, setEdges]);

  useEffect(() => {
    if (editing || agents.length === 0) {
      setActiveAgentId(null);
      return;
    }

    const tick = () => {
      const busy = agents.filter((a) => a.status === "executing" || a.status === "thinking");
      if (busy.length > 0) {
        setActiveAgentId(busy[0].id);
        return;
      }
      simulationIndex.current = (simulationIndex.current + 1) % agents.length;
      setActiveAgentId(agents[simulationIndex.current]?.id ?? null);
    };

    tick();
    const interval = window.setInterval(tick, 3200);
    return () => window.clearInterval(interval);
  }, [agents, editing]);

  useEffect(() => {
    if (saveSignal === 0) return;
    saveLayout(nodesRef.current);
    onSave();
  }, [saveSignal, onSave]);

  const onNodeDragStop = useCallback(() => {
    if (editing) saveLayout(nodesRef.current);
  }, [editing]);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        nodeTypes={flowNodeTypes}
        edgeTypes={edgeTypes}
        nodesDraggable={editing}
        nodesConnectable={false}
        elementsSelectable={editing}
        panOnDrag={editing ? [1, 2] : true}
        panOnScroll
        zoomOnScroll
        zoomOnPinch
        minZoom={0.25}
        maxZoom={1.75}
        fitView
        fitViewOptions={{ padding: 0.22, maxZoom: 1 }}
        proOptions={{ hideAttribution: true }}
        className={editing ? "cursor-default" : "cursor-grab active:cursor-grabbing"}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#c5c5d9" />
        <Controls
          showInteractive={false}
          className="!bg-surface-container-lowest !border-outline-variant/40 !shadow-md !rounded-xl overflow-hidden"
        />
      </ReactFlow>
    </div>
  );
}
