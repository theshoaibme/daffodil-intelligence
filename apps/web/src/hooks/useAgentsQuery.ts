import { useQuery } from "@tanstack/react-query";
import { hubApi } from "../lib/hubApi";

export function useAgentsQuery() {
  return useQuery({
    queryKey: ["agents", "hub"],
    queryFn: () => hubApi.listAgents(),
    staleTime: 30_000,
  });
}
