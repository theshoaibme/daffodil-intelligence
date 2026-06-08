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

import type { Agent } from "../../../hooks/useAgents";
import { useRuntimeStatus } from "../../../hooks/useRuntimeStatus";
import { ActiveBeamEdge } from "./ActiveBeamEdge";
import { AgentDetailDialog } from "./AgentDetailDialog";
import { FlowZoomControls } from "./FlowZoomControls";
import { flowNodeTypes } from "./FlowNodes";
import { buildAgentGraph } from "./graphBuilder";
import { loadLayout, saveLayout } from "./layoutStorage";
import { nextParallelSimulation, type ParallelSimulationState } from "./parallelSimulator";
import { SimulatorPanel } from "./SimulatorPanel";

const edgeTypes = { activeBeam: ActiveBeamEdge };

const EMPTY_SIMULATION: ParallelSimulationState = {
  activeAgentIds: [],
  activeInputId: "input-telegram",
  activeModelId: "gemini-2.0-flash",
  modelActive: false,
  modelTask: "",
  pipelineLabel: "",
  tasks: [],
};

interface AgentFlowCanvasProps {
  agents: Agent[];
  editing: boolean;
  onSave: () => void;
  saveSignal: number;
}

export function AgentFlowCanvas({ agents, editing, onSave, saveSignal }: AgentFlowCanvasProps) {
  const savedLayout = useMemo(() => loadLayout(), []);
  const { runtime } = useRuntimeStatus();
  const [simulation, setSimulation] = useState<ParallelSimulationState>(EMPTY_SIMULATION);
  const [dialogAgents, setDialogAgents] = useState<Agent[] | null>(null);
  const [selectedCount, setSelectedCount] = useState(0);
  const simulationRound = useRef(0);
  const nodesRef = useRef<Node[]>([]);

  const graph = useMemo(
    () =>
      buildAgentGraph(agents, savedLayout, {
        activeAgentIds: simulation.activeAgentIds,
        activeInputId: simulation.activeInputId,
        modelActive: simulation.modelActive,
        activeModelId: simulation.activeModelId,
        engine: runtime.engine,
      }),
    [
      agents,
      savedLayout,
      simulation.activeAgentIds,
      simulation.activeInputId,
      simulation.activeModelId,
      simulation.modelActive,
      runtime.engine,
    ]
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
    if (editing || agents.length === 0) {
      setSimulation(EMPTY_SIMULATION);
      return;
    }

    const tick = () => {
      const next = nextParallelSimulation(agents, simulationRound.current, runtime);
      simulationRound.current += 1;
      setSimulation(next);
    };

    tick();
    const interval = window.setInterval(tick, 3400);
    return () => window.clearInterval(interval);
  }, [agents, editing, runtime]);

  useEffect(() => {
    if (saveSignal === 0) return;
    saveLayout(nodesRef.current);
    onSave();
  }, [saveSignal, onSave]);

  const onNodeDragStop = useCallback(() => {
    if (editing) saveLayout(nodesRef.current);
  }, [editing]);

  const onSelectionChange = useCallback(({ nodes: selectedNodes }: { nodes: Node[] }) => {
    const agentNodes = selectedNodes.filter((n) => n.type === "agent");
    setSelectedCount(agentNodes.length);
  }, []);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (node.type !== "agent") return;

      const agent = agents.find((a) => a.id === node.id);
      if (!agent) return;

      const selectedAgentNodes = nodesRef.current.filter((n) => n.selected && n.type === "agent");
      const selectedIds = selectedAgentNodes.map((n) => n.id);

      if (selectedIds.length > 1 && selectedIds.includes(node.id)) {
        setDialogAgents(
          selectedIds
            .map((id) => agents.find((a) => a.id === id))
            .filter((a): a is Agent => Boolean(a))
        );
      } else {
        setDialogAgents([agent]);
      }
    },
    [agents]
  );

  const onPaneClick = useCallback(() => {
    if (!editing) {
      setDialogAgents(null);
    }
  }, [editing]);

  return (
    <div className="agent-flow-canvas w-full h-full relative">
      {!editing && <SimulatorPanel simulation={simulation} />}

      {selectedCount > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 px-3 py-1.5 rounded-full bg-surface-container-lowest/95 border border-outline-variant/40 shadow-md text-xs font-medium text-on-surface">
          {selectedCount} agents selected — Shift+click to add more, click an agent for details
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onNodeClick={onNodeClick}
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
        fitView
        fitViewOptions={{ padding: 0.22, maxZoom: 1 }}
        proOptions={{ hideAttribution: true }}
        className={editing ? "cursor-default" : "cursor-grab active:cursor-grabbing"}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#c5c5d9" />
        <FlowZoomControls />
      </ReactFlow>

      {dialogAgents && (
        <AgentDetailDialog agents={dialogAgents} onClose={() => setDialogAgents(null)} />
      )}
    </div>
  );
}
