def get_budget_prompt(state: dict, research_text: str) -> str:
    place = state.get("trip_place", "")
    days = state.get("trip_days", 3)
    style = state.get("trip_style", "general")
    budget = state.get("trip_budget", 0)
    return f"""
You are a travel cost estimator. Estimate realistic costs in Indian Rupees (INR)
for the WHOLE trip, using the live research below as guidance.

Destination: {place}
Days: {days}
Travel style: {style} (solo=1, couple=2, family=4, friends group=4 travellers)
User's stated budget: INR {budget if budget and budget > 0 else "not provided"}

Live cost research (from Google):
{research_text}

Return ONLY JSON (no markdown, no prose) with integer INR values:
{{
  "accommodation": int,
  "food": int,
  "local_transport": int,
  "sightseeing": int,
  "intercity_transport": int,
  "total": int,
  "per_day": [int, ...],
  "notes": "one short sentence",
  "status": "ok | tight | over"
}}

Rules:
- "per_day" must contain exactly {days} integers, one realistic spend per day.
  Vary them (arrival/departure days usually differ from full sightseeing days);
  they should sum to total.
- total must equal accommodation + food + local_transport + sightseeing + intercity_transport.
- If the user's budget is clearly below this estimate, set "status" to "over".
"""
