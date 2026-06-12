import { useNavigate } from "react-router-dom";
import { Network, Cpu, Chrome, Server, CheckCircle2 } from "lucide-react";
import { Button, Badge } from "@components/ui";
import { ROUTES } from "@lib";
import { useMcpStatus } from "@hooks";
import { PublicLayout } from "@layout";

export function ConnectionsPage() {
  const navigate = useNavigate();
  const { status: mcpStatusObj, detail: mcpDetail } = useMcpStatus();
  const isConnected = mcpStatusObj.status === "connected";

  return (
    <PublicLayout>
      <main className="max-w-[90rem] mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 sm:py-12 flex-1 flex flex-col justify-center">
        <div className="rounded-[2.5rem] bg-surface-container-lowest p-6 sm:p-10 shadow-sm relative overflow-hidden">
          {/* Subtle gradient accent */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl pointer-events-none" />

          <div className="flex items-start gap-4 sm:gap-6 mb-8 relative z-10">
            <div className="p-4 rounded-3xl bg-primary/10 text-primary shrink-0">
              <Network size={32} />
            </div>
            <div>
              <span className="text-xs font-semibold tracking-wider text-primary uppercase bg-primary/10 px-2.5 py-1 rounded-full">
                Active Connections
              </span>
              <h1 className="text-2xl sm:text-3xl font-medium tracking-tight mt-3 mb-2">
                Integrations & MCP Servers
              </h1>
              <p className="text-on-surface-variant text-sm sm:text-base max-w-2xl leading-relaxed">
                Configure Model Context Protocol (MCP) servers, manage local developer tools, and connect third-party platforms to extend the agent's actions and knowledge.
              </p>
            </div>
          </div>

          <div className="space-y-4 mt-8 relative z-10">
            {/* MCP Integration Item */}
            <div className="rounded-3xl bg-surface-container-low/60 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary mt-1">
                  <Server size={22} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="font-semibold text-base">Model Context Protocol (MCP)</h2>
                    <Badge
                      label={isConnected ? "Connected" : "Disconnected"}
                      className={isConnected ? "bg-emerald-500/10 text-emerald-600 font-semibold" : "bg-red-500/10 text-red-600 font-semibold"}
                    />
                  </div>
                  <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed mt-1">
                    Manage servers supplying tools, resources, and custom capabilities to the agent.
                  </p>
                  {mcpDetail && mcpDetail.servers && mcpDetail.servers.length > 0 && (
                    <div className="mt-3 flex gap-2 flex-wrap">
                      {mcpDetail.servers.map((s: any) => (
                        <span key={s.name} className="inline-flex items-center gap-1 text-[11px] bg-surface-container-high px-2.5 py-1 rounded-full text-on-surface-variant">
                          <CheckCircle2 size={10} className="text-emerald-500" />
                          {s.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <Button
                variant="tonal"
                size="sm"
                onClick={() => navigate(`${ROUTES.home}?agents=1`)}
                className="shrink-0"
              >
                Configure Servers
              </Button>
            </div>

            {/* Google OAuth Integration Item */}
            <div className="rounded-3xl bg-surface-container-low/60 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary mt-1">
                  <Chrome size={22} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="font-semibold text-base">Google Integration</h2>
                    <Badge label="Available" className="bg-primary/10 text-primary font-semibold" />
                  </div>
                  <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed mt-1">
                    Access Google Classroom, Drive documents, Calendar events, and Chrome tools.
                  </p>
                </div>
              </div>
              <Button
                variant="outlined"
                size="sm"
                onClick={() => navigate(ROUTES.account)}
                className="shrink-0"
              >
                Manage Google
              </Button>
            </div>

            {/* Workspace Agent Runtime Item */}
            <div className="rounded-3xl bg-surface-container-low/60 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-2xl bg-primary/10 text-primary mt-1">
                  <Cpu size={22} />
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="font-semibold text-base">Local Agent Runtime</h2>
                    <Badge label="Running" className="bg-emerald-500/10 text-emerald-600 font-semibold" />
                  </div>
                  <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed mt-1">
                    Executes system commands, browser actions, file system operations, and background subagents.
                  </p>
                </div>
              </div>
              <Button
                variant="outlined"
                size="sm"
                onClick={() => navigate(ROUTES.guidance)}
                className="shrink-0"
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
