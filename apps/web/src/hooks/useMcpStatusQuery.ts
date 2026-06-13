import { useQuery } from "@tanstack/react-query";
import { fetchMcpStatusDetail } from "../lib/mcpApi";

export function useMcpStatusQuery() {
  return useQuery({
    queryKey: ["mcp", "status"],
    queryFn: fetchMcpStatusDetail,
    staleTime: 10_000,
  });
}
