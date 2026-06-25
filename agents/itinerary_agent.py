"""
Itinerary (composer) agent — final step.

Uses the LLM to write a warm, guided, day-by-day plan (Morning / Afternoon /
Evening with explanations), grounded on everything the other agents fetched.
Per-day costs come from the budget breakdown, so they vary by day.
"""

from services.llm import call_gemini


def itinerary_agent(state: dict) -> dict:
    print("running itinerary (composer) agent")
    place = state.get("trip_place", "")
    dates = state.get("trip_dates", "Not specified")
    days = state.get("trip_days", 3)
    style = state.get("trip_style", "general")
    budget = state.get("trip_budget", 0)
    cb = state.get("cost_breakdown") or {}
    warnings = state.get("warnings", [])

    if not place:
        state["final_itinerary"] = "Please provide a destination to generate an itinerary."
        return state

    per_day_txt = ""
    if cb.get("per_day"):
        per_day_txt = "Use these per-day spend figures (they vary by day): " + \
            ", ".join(f"Day {i+1} = Rs {c}" for i, c in enumerate(cb["per_day"]))

    prompt = f"""
You are a friendly, practical travel planner. Write a guided, day-by-day itinerary
in Markdown for a {days}-day {style} trip to {place} ({dates}).

Use ONLY the real information gathered below (do not invent famous places):

BEST TIME TO VISIT:
{state.get('best_time', 'Not available')}

WEATHER:
{state.get('weather_info', 'Not available')}

TOP PLACES (from live search):
{state.get('place_info', 'Not available')}

TRANSPORT (from live search):
{state.get('transport_info', 'Not available')}

BUDGET BREAKDOWN:
{state.get('budget_info', 'Not available')}

User's budget: INR {budget if budget and budget > 0 else 'not provided'}.
{per_day_txt}

FORMAT (strict):
For each day use a header line exactly like '### Day 1 - <short theme>' and then:
- **Morning:** what to do and why (1-2 sentences)
- **Afternoon:** ...
- **Evening:** ...
- **Stay:** suggested area to stay
- **Approx cost:** Rs <use the per-day figure for that day>

Day 1 morning should be arrival/check-in; the final day should include departure.
Spread the real places sensibly across the days and respect the weather.

After the days, add a section '## 💰 Expense Summary' with a Markdown table of
Accommodation, Food, Local transport, Sightseeing, Intercity travel and the Total
(use the budget breakdown figures), then one line saying whether it fits the budget.

End with '## Why these choices?' — explain the key reasoning in 2-3 lines.
"""
    itinerary = call_gemini(prompt)
    state["final_itinerary"] = itinerary or "Could not generate the itinerary (LLM unavailable)."
    state["warnings"] = warnings
    state.setdefault("trace", []).append({
        "step": "Itinerary (composer)",
        "source": "Gemini",
        "output": f"{days}-day itinerary composed",
    })
    return state
