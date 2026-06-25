# """
# Destination agent — fetches top places to visit live from Serper (Google).
# No hard-coded attractions.
# """

# from services.serper_service import search_serper


# def destination_agent(state: dict) -> dict:
#     print("running destination agent (Serper)")
#     place = state.get("trip_place", "")
#     dates = state.get("trip_dates", "Not specified")
#     style = state.get("trip_style", "general")
#     days = state.get("trip_days", 3)
#     warnings = state.get("warnings", [])

#     if not place:
#         state["place_info"] = "Destination details not available."
#         state["warnings"] = warnings
#         return state

#     query = f"top tourist places to visit in {place} for a {days}-day {style} trip in {dates}"
#     data = search_serper(query, num_results=6)

#     if "error" in data or not data.get("organic"):
#         state["place_info"] = f"Could not fetch live places for {place}."
#         warnings.append(f"No live destination results for {place}.")
#         state["warnings"] = warnings
#         state.setdefault("trace", []).append(
#             {"step": "Destination", "source": "Serper", "output": "no results"})
#         return state

#     summary = f"Top places to explore in {place}:\n\n"
#     for i, r in enumerate(data["organic"][:6], start=1):
#         summary += f"{i}. {r.get('title', '')}\n   {r.get('snippet', '')}\n"

#     state["place_info"] = summary.strip()
#     state["warnings"] = warnings
#     state.setdefault("trace", []).append({
#         "step": "Destination (top places)",
#         "source": "Serper (Google)",
#         "output": [r.get("title", "") for r in data["organic"][:6]],
#     })
#     return state



"""
Destination agent — uses Serper for live search and Gemini for cleanup.

Flow:
1. Serper fetches live Google search results.
2. Gemini converts raw search results into clean tourist places.
3. Final clean output is stored in state["place_info"].
"""

from services.serper_service import search_serper
from services.llm import call_gemini


def destination_agent(state: dict) -> dict:
    print("running destination agent (Serper + Gemini only)")

    # Mark current agent for debugging/UI if needed
    state["current_agent"] = "destination"

    place = state.get("trip_place", "")
    days = state.get("trip_days", 3)
    style = state.get("trip_style", "general")
    dates = state.get("trip_dates", "Not specified")

    warnings = state.setdefault("warnings", [])
    trace = state.setdefault("trace", [])

    if not place:
        state["place_info"] = "Destination details not available."

        trace.append({
            "step": "Destination",
            "source": "Serper + Gemini",
            "output": state["place_info"]
        })

        return state

    query = (
        f"best places to visit in {place}, top tourist attractions, "
        f"famous landmarks, beaches, forts, museums, markets and things to do "
        f"for a {days}-day {style} trip in {dates}"
    )

    print("Destination search query:", query)

    serper_data = search_serper(query, num_results=10)

    if "error" in serper_data or not serper_data.get("organic"):
        state["place_info"] = f"Could not fetch live destination results for {place}."
        warnings.append(f"No live destination results for {place}.")

        trace.append({
            "step": "Destination",
            "source": "Serper",
            "query": query,
            "output": state["place_info"],
            "error": serper_data.get("error")
        })

        return state

    raw_results_text = ""

    for index, result in enumerate(serper_data.get("organic", [])[:10], start=1):
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        link = result.get("link", "")

        raw_results_text += f"{index}. Title: {title}\n"
        raw_results_text += f"   Snippet: {snippet}\n"
        raw_results_text += f"   Source: {link}\n\n"

    prompt = f"""
You are a travel destination expert.

I have live web search results from Serper for this trip.

Trip details:
- Destination: {place}
- Number of days: {days}
- Trip style: {style}
- Travel dates: {dates}

Raw Serper search results:
{raw_results_text}

Your task:
Convert these raw search results into a clean list of actual tourist places to visit in {place}.

Rules:
- Do NOT include article titles.
- Do NOT include blog names.
- Do NOT include website names.
- Do NOT include URLs.
- Do NOT mention source names.
- Extract only real tourist places, attractions, landmarks, beaches, forts, museums, markets, viewpoints, gardens, lakes, temples, churches, or local areas.
- If the search result mentions multiple places, separate them into individual tourist places.
- Include 6 to 8 places if possible.
- Each place should have one short practical reason to visit.
- Make the output useful for a final itinerary.

Output format exactly:

Top places to explore in {place}:

1. Place Name
   Short reason to visit.

2. Place Name
   Short reason to visit.
"""

    print("===== SENDING SERPER RAW RESULTS TO GEMINI =====")

    gemini_output = call_gemini(prompt)

    if gemini_output:
        state["place_info"] = gemini_output.strip()
        source_used = "Serper + Gemini"
    else:
        state["place_info"] = f"Could not clean destination results for {place} using Gemini."
        warnings.append("Gemini cleanup failed or quota exhausted.")
        source_used = "Serper + Gemini failed"

    # Store raw Serper results for debugging only
    state["destination_raw_results"] = serper_data.get("organic", [])[:10]

    # IMPORTANT:
    # UI should read this "output" key.
    # Earlier only output_preview was there, so UI showed None.
    trace.append({
        "step": "Destination",
        "source": source_used,
        "query": query,
        "raw_results_count": len(serper_data.get("organic", [])),
        "output": state["place_info"],
        "output_preview": state["place_info"][:300]
    })

    state["warnings"] = warnings

    print("===== DESTINATION STATE UPDATED =====")
    print(state["place_info"])

    return state
