import { useEffect } from "react";
import { CopycatToolbar } from "./components/CopycatToolbar";
import { useCopycatMode } from "./hooks/useCopycatMode";
import { CopycatAuthProvider, useCopycatAuth } from "./context/AuthContext";
import { LoginPage } from "./components/LoginPage";
import { HashRouter } from "react-router-dom";

function CopycatDock() {
  const { isAuthenticated, login } = useCopycatAuth();
  const state = useCopycatMode(isAuthenticated); // Only connect if authenticated

  // Ensure Electron window allows mouse interactions on the Login screen
  useEffect(() => {
    if (!isAuthenticated && typeof window !== "undefined") {
      window.electronAPI?.setIgnoreMouse?.(false);
    }
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return <LoginPage onLogin={login} />;
  }

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
            void state.stopRecording();
          } else {
            void state.startRecording();
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
      <CopycatAuthProvider>
        <CopycatDock />
      </CopycatAuthProvider>
    </HashRouter>
  );
}

export default App;
