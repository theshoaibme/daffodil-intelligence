import { useNavigate } from "react-router-dom";
import { Network, Cpu, Chrome, Server, CheckCircle2 } from "lucide-react";
import { Button, Badge } from "@components/ui";
import { PUBLIC_LAYOUT_WIDTH, ROUTES } from "@lib";
import { useMcpStatus } from "@hooks";
import { PublicLayout } from "@layout";

export function ConnectionsPage() {
  const navigate = useNavigate();
  const { status: mcpStatusObj, detail: mcpDetail } = useMcpStatus();
  const isConnected = mcpStatusObj.status === "connected";

  return (
    <PublicLayout>
      <main className={`${PUBLIC_LAYOUT_WIDTH} py-8 sm:py-12 flex-1 flex flex-col justify-center`}>
        <div className="rounded-[2.5rem] bg-surface-container-lowest p-6 sm:p-10 shadow-sm relative overflow-hidden">
          {/* Subtle gradient accent */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-start gap-4 sm:gap-6 mb-8 relative z-10">
            <div className="p-4 rounded-3xl bg-primary/10 text-primary shrink-0">
              <Network size={36} />
            </div>
            <div>
              <span className="text-xs sm:text-sm font-semibold tracking-wider text-primary uppercase bg-primary/10 px-3 py-1 rounded-full">
                Active Connections
              </span>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight mt-4 mb-3">
                Integrations & MCP Servers
              </h1>
              <p className="text-on-surface-variant text-base sm:text-lg max-w-4xl leading-relaxed">
                Configure Model Context Protocol (MCP) servers, manage local developer tools, and connect third-party platforms to extend the agent's actions and knowledge.
              </p>
            </div>
          </div>

          <div className="space-y-4 mt-8 relative z-10">
            {/* MCP Integration Item */}
            <div className="rounded-3xl bg-surface-container-low/60 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary mt-1">
                  <Server size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="font-semibold text-lg sm:text-xl">Model Context Protocol (MCP)</h2>
                    <Badge
                      label={isConnected ? "Connected" : "Disconnected"}
                      className={isConnected ? "bg-emerald-500/10 text-emerald-600 font-semibold text-xs px-2.5 py-0.5" : "bg-red-500/10 text-red-600 font-semibold text-xs px-2.5 py-0.5"}
                    />
                  </div>
                  <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed mt-1.5">
                    Manage servers supplying tools, resources, and custom capabilities to the agent.
                  </p>
                  {mcpDetail && mcpDetail.servers && mcpDetail.servers.length > 0 && (
                    <div className="mt-3 flex gap-2 flex-wrap">
                      {mcpDetail.servers.map((s: any) => (
                        <span key={s.name} className="inline-flex items-center gap-1.5 text-[12px] sm:text-xs bg-surface-container-high px-3 py-1 rounded-full text-on-surface-variant">
                          <CheckCircle2 size={11} className="text-emerald-500" />
                          {s.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="tonal"
                size="md"
                onClick={() => navigate(`${ROUTES.home}?agents=1`)}
                className="shrink-0 rounded-full"
              >
                Configure Servers
              </Button>
            </div>

            {/* Google OAuth Integration Item */}
            <div className="rounded-3xl bg-surface-container-low/60 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary mt-1">
                  <Chrome size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="font-semibold text-lg sm:text-xl">Google Integration</h2>
                    <Badge label="Available" className="bg-primary/10 text-primary font-semibold text-xs px-2.5 py-0.5" />
                  </div>
                  <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed mt-1.5">
                    Access Google Classroom, Drive documents, Calendar events, and Chrome tools.
                  </p>
                </div>
              </div>
              <Button
                variant="outlined"
                size="md"
                onClick={() => navigate(ROUTES.account)}
                className="shrink-0 rounded-full"
              >
                Manage Google
              </Button>
            </div>

            {/* Workspace Agent Runtime Item */}
            <div className="rounded-3xl bg-surface-container-low/60 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary mt-1">
                  <Cpu size={24} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="font-semibold text-lg sm:text-xl">Local Agent Runtime</h2>
                    <Badge label="Running" className="bg-emerald-500/10 text-emerald-600 font-semibold text-xs px-2.5 py-0.5" />
                  </div>
                  <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed mt-1.5">
                    Executes system commands, browser actions, file system operations, and background subagents.
                  </p>
                </div>
              </div>
              <Button
                variant="outlined"
                size="md"
                onClick={() => navigate(ROUTES.guidance)}
                className="shrink-0 rounded-full"
              >
                Runtime Docs
              </Button>
            </div>
          </div>
        </div>
      </main>
    </PublicLayout>
  );
}
