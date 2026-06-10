import ComputerView from "@components/features/ComputerView";
import { AuthProvider } from "@context";
import { HashRouter } from "react-router-dom";

function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <div className="relative w-screen h-screen overflow-hidden bg-background">
          <ComputerView embedded={false} />
        </div>
      </AuthProvider>
    </HashRouter>
  );
}

export default App;
