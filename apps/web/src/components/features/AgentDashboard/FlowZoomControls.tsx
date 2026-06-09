import { Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import { Panel, useReactFlow } from "@xyflow/react";
import { FLOW_FIT_OPTIONS } from "./flowLayout";

export function FlowZoomControls({ belowHeader = false }: { belowHeader?: boolean }) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  return (
    <Panel
      position={belowHeader ? "bottom-left" : "top-left"}
      className={`!z-20 flex items-center gap-1 rounded-xl bg-surface-container-lowest/95 border border-outline-variant/40 shadow-md p-1 ${
        belowHeader ? "!m-4 sm:!m-6" : "!m-4"
      }`}
    >
      <button
        type="button"
        onClick={() => zoomIn()}
        className="p-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors"
        aria-label="Zoom in"
      >
        <ZoomIn size={16} />
      </button>
      <button
        type="button"
        onClick={() => zoomOut()}
        className="p-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors"
        aria-label="Zoom out"
      >
        <ZoomOut size={16} />
      </button>
      <button
        type="button"
        onClick={() => fitView(FLOW_FIT_OPTIONS)}
        className="p-2 rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors"
        aria-label="Fit view"
      >
        <Maximize2 size={16} />
      </button>
    </Panel>
  );
}
