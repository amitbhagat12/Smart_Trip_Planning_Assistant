# """
# Smart selective workflow.

# First run:  planner → weather → destination → transport → budget → itinerary
# Re-run:     planner → only agents whose inputs changed → itinerary (if anything ran)

# The graph is rebuilt each turn so we can wire only the required agents.
# Agents NOT in the run-list are skipped; their cached outputs stay in state.
# """

# from langgraph.graph import StateGraph, END
# from graph.state import TripState
# from graph.replan import agents_to_run, detect_changed_fields, describe_replan

# from agents.planner import planner_agent
# from agents.weather_agent import weather_agent
# from agents.destination_agent import destination_agent
# from agents.transport_agent import transport_agent
# from agents.budget_agent import budget_agent
# from agents.itinerary_agent import itinerary_agent

# AGENT_FN = {
#     "weather":     weather_agent,
#     "destination": destination_agent,
#     "transport":   transport_agent,
#     "budget":      budget_agent,
#     "itinerary":   itinerary_agent,
# }


# def route_after_planner(state: dict) -> str:
#     return "ask_user" if state.get("need_clarification") else "proceed"


# def build_graph(agents: list = None):
#     """
#     Build (and compile) a LangGraph workflow.

#     agents: ordered list of agent names to include.
#             Defaults to all agents (first-run / full plan).
#     """
#     if agents is None:
#         agents = list(AGENT_FN.keys())  # ["weather","destination","transport","budget","itinerary"]

#     graph = StateGraph(TripState)
#     graph.add_node("planner", planner_agent)

#     for name in agents:
#         graph.add_node(name, AGENT_FN[name])

#     graph.set_entry_point("planner")

#     if agents:
#         graph.add_conditional_edges(
#             "planner", route_after_planner,
#             {"ask_user": END, "proceed": agents[0]},
#         )
#         for i in range(len(agents) - 1):
#             graph.add_edge(agents[i], agents[i + 1])
#         graph.add_edge(agents[-1], END)
#     else:
#         # Nothing to run — planner alone
#         graph.add_conditional_edges(
#             "planner", route_after_planner,
#             {"ask_user": END, "proceed": END},
#         )

#     return graph.compile()


# def invoke_smart(current_state: dict, prev_state: dict) -> tuple[dict, str]:
#     """
#     Entry point called from app.py.

#     Returns:
#         (result_state, replan_message)
#     """
#     is_first_run = not prev_state.get("final_itinerary") and not prev_state.get("place_info")

#     if is_first_run:
#         changed = set()
#     else:
#         changed = detect_changed_fields(prev_state, current_state)

#     agents = agents_to_run(changed, is_first_run)
#     replan_msg = describe_replan(changed, agents)

#     print(f"\n[Replan] {replan_msg}")
#     print(f"[Replan] Agents in this run: {agents}\n")

#     graph = build_graph(agents)
#     result = graph.invoke(current_state)

#     # Store replan metadata in state so the UI can show it
#     result["_replan_agents"] = agents
#     result["_replan_message"] = replan_msg
#     result["_changed_fields"] = list(changed)

#     return result, replan_msg


# # Keep backward-compatible build_graph() used by __main__
# if __name__ == "__main__":
#     try:
#         build_graph().get_graph().draw_mermaid_png(output_file_path="graph_diagram.png")
#         print("Saved graph_diagram.png")
#     except Exception as e:
#         print("Could not render diagram:", e)

from langgraph.graph import StateGraph, END

from graph.state import TripState
from graph.replan import agents_to_run, detect_changed_fields, describe_replan

from agents.planner import planner_agent
from agents.weather_agent import weather_agent
from agents.destination_agent import destination_agent
from agents.transport_agent import transport_agent
from agents.budget_agent import budget_agent
from agents.itinerary_agent import itinerary_agent


AGENT_FN = {
    "weather": weather_agent,
    "destination": destination_agent,
    "transport": transport_agent,
    "budget": budget_agent,
    "itinerary": itinerary_agent,
}


# ✅ Route after planner
def route_after_planner(state: dict) -> str:
    return "ask_user" if state.get("need_clarification") else "proceed"


# ✅ Build dynamic graph
def build_graph(agents: list = None):
    if agents is None:
        agents = list(AGENT_FN.keys())

    graph = StateGraph(TripState)

    graph.add_node("planner", planner_agent)

    for name in agents:
        graph.add_node(name, AGENT_FN[name])

    graph.set_entry_point("planner")

    if agents:
        graph.add_conditional_edges(
            "planner",
            route_after_planner,
            {
                "ask_user": END,
                "proceed": agents[0],
            },
        )

        for i in range(len(agents) - 1):
            graph.add_edge(agents[i], agents[i + 1])

        graph.add_edge(agents[-1], END)
    else:
        graph.add_conditional_edges(
            "planner",
            route_after_planner,
            {
                "ask_user": END,
                "proceed": END,
            },
        )

    return graph.compile()


# ✅ ✅ MAIN SMART EXECUTION FUNCTION
def invoke_smart(current_state: dict, prev_state: dict):
    # ✅ FIX 1: Proper first-run detection
    is_first_run = not bool(prev_state)

    if is_first_run:
        changed = set()
    else:
        changed = detect_changed_fields(prev_state, current_state)

    agents = agents_to_run(changed, is_first_run)
    replan_msg = describe_replan(changed, agents)

    print(f"\n[Replan] {replan_msg}")
    print(f"[Replan] Agents running: {agents}\n")

    # ✅ FIX 2: Merge states BEFORE execution
    merged_state = {**prev_state, **current_state}

    graph = build_graph(agents)
    result = graph.invoke(merged_state)

    # ✅ FIX 3: Restore skipped outputs (cache)
    for agent in AGENT_FN.keys():
        if agent not in agents:
            if agent in prev_state:
                result[agent] = prev_state[agent]

    # ✅ Metadata for UI/debug
    result["_replan_agents"] = agents
    result["_replan_message"] = replan_msg
    result["_changed_fields"] = list(changed)

    return result, replan_msg


# ✅ Optional: graph visualization
if __name__ == "__main__":
    try:
        build_graph().get_graph().draw_mermaid_png(
            output_file_path="graph_diagram.png"
        )
        print("✅ Graph saved as graph_diagram.png")
    except Exception as e:
        print("❌ Could not render diagram:", e)
