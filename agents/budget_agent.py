"""
Budget agent — LLM-based cost estimate (grounded with live Serper research).
No hard-coded per-day cost tables.
"""

from services.serper_service import search_serper
from services.llm import call_gemini, extract_json
from prompts.budget_prompt import get_budget_prompt


def _titles(data: dict, n: int = 3) -> str:
    if not isinstance(data, dict) or "error" in data:
        return ""
    return "\n".join(f"- {r.get('title', '')}: {r.get('snippet', '')}"
                     for r in (data.get("organic") or [])[:n])


def budget_agent(state: dict) -> dict:
    print("running budget agent (Serper research + LLM estimate)")
    place = state.get("trip_place", "")
    days = state.get("trip_days", 3) or 3
    budget = state.get("trip_budget", 0) or 0
    warnings = state.get("warnings", [])

    if not place:
        state["budget_info"] = "Budget details not available."
        state["warnings"] = warnings
        return state

    # Live cost research to ground the LLM estimate.
    research = "\n".join([
        _titles(search_serper(f"average hotel cost per night in {place}", 3)),
        _titles(search_serper(f"average daily food cost for tourists in {place}", 3)),
        _titles(search_serper(f"tourist activity and sightseeing cost in {place}", 3)),
    ]).strip() or "No live cost data available."

    data = extract_json(call_gemini(get_budget_prompt(state, research)))
    cats = ["accommodation", "food", "local_transport", "sightseeing", "intercity_transport"]

    if isinstance(data, dict) and all(k in data for k in cats):
        try:
            data["total"] = sum(int(data.get(c, 0)) for c in cats)
        except Exception:
            data["total"] = data.get("total")
        # Normalise per_day so it varies and sums to total.
        pd = data.get("per_day")
        if (isinstance(pd, list) and len(pd) == days
                and all(isinstance(x, (int, float)) and x > 0 for x in pd)
                and isinstance(data.get("total"), int)):
            s = sum(pd)
            pd = [max(1, round(x * data["total"] / s)) for x in pd]
            pd[-1] += data["total"] - sum(pd)
            data["per_day"] = pd
        else:
            data["per_day"] = None
        state["cost_breakdown"] = data

        if budget and isinstance(data.get("total"), int) and data["total"] > budget:
            warnings.append("Estimated cost is higher than your stated budget.")

        lines = [f"Budget estimate for {place} ({days} days):", ""]
        for label, key in [("Accommodation", "accommodation"), ("Food", "food"),
                           ("Local transport", "local_transport"),
                           ("Sightseeing", "sightseeing"),
                           ("Intercity travel", "intercity_transport")]:
            lines.append(f"- {label}: Rs {int(data.get(key, 0)):,}")
        lines.append(f"- Total: Rs {int(data['total']):,}")
        if data.get("per_day"):
            lines.append("- Per day: " + ", ".join(f"Day {i+1} Rs {c:,}"
                                                    for i, c in enumerate(data["per_day"])))
        if data.get("notes"):
            lines.append(f"- Note: {data['notes']}")
        state["budget_info"] = "\n".join(lines)
    else:
        state["budget_info"] = "Could not estimate the budget (LLM unavailable)."
        state["cost_breakdown"] = {}
        warnings.append("Budget estimate unavailable — check GEMINI_API_KEY.")

    state["warnings"] = warnings
    state.setdefault("trace", []).append({
        "step": "Budget (LLM estimate)",
        "source": "Serper research + Gemini",
        "output": state.get("cost_breakdown") or state["budget_info"],
    })
    return state
