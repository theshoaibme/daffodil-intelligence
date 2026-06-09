from langgraph.graph import StateGraph, END
from typing import TypedDict, List
import logging

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    message: str
    user_id: int
    agents: List[str]
    results: dict
    final_response: str
    tools_used: List[str]


def create_graph():
    graph = StateGraph(AgentState)

    graph.add_node("route", route_to_agents)
    graph.add_node("execute", execute_agents)
    graph.add_node("synthesize", synthesize_response)

    graph.set_entry_point("route")
    graph.add_edge("route", "execute")
    graph.add_edge("execute", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


async def route_to_agents(state: AgentState) -> AgentState:
    from ..agents.supervisor import detect_intent
    agents = detect_intent(state["message"])
    state["agents"] = agents
    logger.info(f"Routed to agents: {agents}")
    return state


async def execute_agents(state: AgentState) -> AgentState:
    from ..agents.supervisor import process_with_agents, AGENT_MAP
    results = {}
    tools_used = []

    for agent_type in state["agents"]:
        if agent_type in AGENT_MAP:
            try:
                agent = AGENT_MAP[agent_type]
                response = await agent.process(state["message"])
                results[agent_type] = response
                tools_used.extend(agent.tools)
            except Exception as e:
                logger.error(f"Agent {agent_type} failed: {e}")
                results[agent_type] = str(e)

    state["results"] = results
    state["tools_used"] = list(set(tools_used))
    return state


async def synthesize_response(state: AgentState) -> AgentState:
    from ..agents.supervisor import synthesize_response
    final = await synthesize_response(state["results"], state["message"])
    state["final_response"] = final
    return state


di_graph = create_graph()