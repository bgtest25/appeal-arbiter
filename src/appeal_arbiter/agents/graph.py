from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from appeal_arbiter.agents.specialists import evidence_node, policy_node, precedent_node
from appeal_arbiter.agents.state import AppealState
from appeal_arbiter.agents.supervisor import supervisor_node
from appeal_arbiter.fixtures.appeal_cases import AppealInput


def build_graph() -> CompiledStateGraph:
    graph = StateGraph(AppealState)
    graph.add_node("evidence", evidence_node)
    graph.add_node("policy", policy_node)
    graph.add_node("precedent", precedent_node)
    graph.add_node("supervisor", supervisor_node)

    graph.add_edge(START, "evidence")
    graph.add_edge(START, "policy")
    graph.add_edge(START, "precedent")
    graph.add_edge("evidence", "supervisor")
    graph.add_edge("policy", "supervisor")
    graph.add_edge("precedent", "supervisor")
    graph.add_edge("supervisor", END)

    return graph.compile()


_graph: CompiledStateGraph | None = None


def get_graph() -> CompiledStateGraph:
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_appeal(case: AppealInput) -> AppealState:
    return get_graph().invoke({"case": case})
