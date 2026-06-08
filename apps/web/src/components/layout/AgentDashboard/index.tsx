import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { Check, Pencil, RefreshCw, X } from "lucide-react";
import { useAgents } from "../../../hooks/useAgents";
import { ROUTES } from "../../../lib/routes";
import { AgentFlowCanvas } from "./AgentFlowCanvas";
import { clearLayout } from "./layoutStorage";

export default function AgentDashboard() {
  const { agents, loading, error, refetch } = useAgents();
  const [editing, setEditing] = useState(false);
  const [saveSignal, setSaveSignal] = useState(0);
  const [savedToast, setSavedToast] = useState(false);

  const handleSave = useCallback(() => {
    setSavedToast(true);
    window.setTimeout(() => setSavedToast(false), 2000);
  }, []);

  const enterEdit = () => setEditing(true);

  const saveAndExit = () => {
    setSaveSignal((n) => n + 1);
    setEditing(false);
  };

  const cancelEdit = () => {
    setEditing(false);
  };

  const resetLayout = () => {
    clearLayout();
    window.location.reload();
  };

  return (
    <div className="flex flex-col h-screen bg-[#f4f2ff] overflow-hidden relative">
      <div className="absolute top-4 right-4 z-30 flex items-center gap-2">
        <Link
          to={ROUTES.home}
          className="hidden sm:inline-flex text-xs font-medium text-on-surface-variant hover:text-on-surface px-3 py-2 rounded-lg"
        >
          Back
        </Link>

        {!editing ? (
          <>
            <button
              type="button"
              onClick={() => refetch()}
              className="p-2 rounded-xl text-on-surface-variant hover:bg-surface-container-lowest/80 transition-colors"
              aria-label="Refresh agents"
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            </button>
            <button
              type="button"
              onClick={enterEdit}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-on-surface bg-surface-container-lowest/90 border border-outline-variant/40 shadow-sm hover:bg-surface-container-lowest transition-colors"
            >
              <Pencil size={15} />
              Edit
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              onClick={resetLayout}
              className="px-3 py-2 rounded-xl text-xs font-medium text-on-surface-variant hover:bg-surface-container-lowest/80"
            >
              Reset layout
            </button>
            <button
              type="button"
              onClick={cancelEdit}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium text-on-surface-variant hover:bg-surface-container-lowest/80"
            >
              <X size={15} />
              Cancel
            </button>
            <button
              type="button"
              onClick={saveAndExit}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-b from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 border-none shadow-sm"
            >
              <Check size={15} />
              Save
            </button>
          </>
        )}
      </div>

      {savedToast && (
        <div className="absolute top-16 right-4 z-40 px-4 py-2 rounded-xl bg-surface-container-lowest border border-outline-variant/40 text-sm text-on-surface shadow-md">
          Layout saved
        </div>
      )}

      <div className="flex-1 min-h-0">
        <AgentFlowCanvas
          agents={agents}
          editing={editing}
          onSave={handleSave}
          saveSignal={saveSignal}
        />
      </div>

      {loading && agents.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#f4f2ff]/80 z-50">
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
  );
}
