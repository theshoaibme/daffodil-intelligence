import { Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import { Panel, useReactFlow } from "@xyflow/react";
import { FLOW_FIT_OPTIONS } from "./flowLayout";

export function FlowZoomControls() {
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  return (
    <Panel position="top-left" className="!m-4 !z-20 flex items-center gap-1 rounded-xl bg-surface-container-lowest/95 border border-outline-variant/40 shadow-md p-1">
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
