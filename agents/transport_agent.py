"""
Transport agent — fetches how to reach + get around live from Serper.
No hard-coded transport rules; the budget/itinerary agents handle reasoning.
"""

from services.serper_service import search_serper


def _snippets(data: dict, n: int = 3) -> str:
    if not isinstance(data, dict) or "error" in data:
        return "- Live data not available.\n"
    out = ""
    for r in (data.get("organic") or [])[:n]:
        out += f"- {r.get('title', '')}: {r.get('snippet', '')}\n"
    return out or "- No results.\n"


def transport_agent(state: dict) -> dict:
    print("running transport agent (Serper)")
    place = state.get("trip_place", "")
    warnings = state.get("warnings", [])

    if not place:
        state["transport_info"] = "Transport details not available."
        state["warnings"] = warnings
        return state

    reach = search_serper(f"how to reach {place} by flight train bus", num_results=3)
    local = search_serper(f"local transport options for tourists in {place}", num_results=3)

    state["transport_info"] = (
        f"Getting to {place}:\n{_snippets(reach)}\n"
        f"Getting around {place}:\n{_snippets(local)}"
    ).strip()
    state["warnings"] = warnings
    state.setdefault("trace", []).append({
        "step": "Transport",
        "source": "Serper (Google)",
        "output": state["transport_info"][:300],
    })
    return state
