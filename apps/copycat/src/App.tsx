import { CopycatToolbar } from "./components/CopycatToolbar";
import { useCopycatMode } from "./hooks/useCopycatMode";
import { AuthProvider } from "@context";
import { HashRouter } from "react-router-dom";

function CopycatDock() {
  const state = useCopycatMode(true); // Auto-connect to daemon

  return (
    <div className="relative w-full h-full bg-transparent overflow-hidden">
      <CopycatToolbar
        connected={state.connected}
        streaming={state.streaming}
        clickMode={state.clickMode}
        keyboardOpen={state.keyboardOpen}
        isRecording={state.isRecording}
        isReplaying={state.isReplaying}
        copycatBlocked={state.copycatBlocked}
        kitOnline={state.kitOnline}
        permissions={state.permissions}
        focusMode={state.focusMode}
        onStreamToggle={state.toggleStream}
        onClickModeToggle={state.toggleClickMode}
        onKeyboardToggle={state.toggleKeyboard}
        onRecordToggle={() => {
          if (state.isRecording) {
            state.stopRecording();
          } else {
            state.startRecording();
          }
        }}
        onReplay={state.replayRecording}
        onFocusToggle={state.toggleFocusMode}
        onChat={() => state.sendChatAction("redirect")}
      />
    </div>
  );
}

function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <CopycatDock />
      </AuthProvider>
    </HashRouter>
  );
}

export default App;
