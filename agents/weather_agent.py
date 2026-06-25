"""
Weather agent — fetches current weather + month outlook + best time to visit.

Uses:
1. OpenWeather for live current weather.
2. Serper for month/season outlook.
3. Serper for best time to visit.

No Gemini call here, to save quota.
"""

from services.weather_service import get_weather
from services.serper_service import search_serper


def clean_snippet(text: str) -> str:
    """
    Cleans Serper snippet text.
    Keeps it simple. No LLM used.
    """
    if not text:
        return ""

    text = text.strip()

    # Remove incomplete trailing ...
    if text.endswith("..."):
        text = text[:-3].strip()

    # Ensure it ends cleanly
    if text and not text.endswith((".", "!", "?")):
        text += "."

    return text


def _first_snippet(data: dict) -> str:
    """
    Extracts the first useful snippet from Serper response.
    Priority:
    1. answerBox answer
    2. answerBox snippet
    3. first organic result snippet
    """
    if not isinstance(data, dict) or "error" in data:
        return ""

    answer_box = data.get("answerBox") or {}

    if answer_box.get("answer"):
        return clean_snippet(answer_box["answer"])

    if answer_box.get("snippet"):
        return clean_snippet(answer_box["snippet"])

    organic_results = data.get("organic") or []

    if organic_results:
        return clean_snippet(organic_results[0].get("snippet", ""))

    return ""


def build_weather_advice(place: str, dates: str, live: dict, month_txt: str) -> str:
    """
    Creates practical travel advice based on available weather information.
    This is rule-based and does not call Gemini.
    """

    advice = []

    description = ""
    temp = None
    humidity = None

    if isinstance(live, dict) and "error" not in live:
        description = str(live.get("description", "")).lower()
        temp = live.get("temp_celsius")
        humidity = live.get("humidity")

    # General useful advice
    advice.append("Check the forecast again closer to the travel date for more accurate planning.")

    # Temperature-based advice
    if temp is not None:
        try:
            temp_value = float(temp)

            if temp_value >= 30:
                advice.append("Carry light cotton clothes, sunscreen, sunglasses, and stay hydrated.")
            elif 20 <= temp_value < 30:
                advice.append("Weather looks comfortable for sightseeing and outdoor activities.")
            elif temp_value < 20:
                advice.append("Carry a light jacket or warm layer, especially for mornings and evenings.")
        except Exception:
            pass

    # Rain/cloud advice
    if "rain" in description or "drizzle" in description:
        advice.append("Carry an umbrella or raincoat and keep some indoor backup activities.")
    elif "cloud" in description or "overcast" in description:
        advice.append("Outdoor plans are still possible, but keep a flexible schedule in case weather changes.")

    # Humidity advice
    if humidity is not None:
        try:
            humidity_value = float(humidity)

            if humidity_value >= 75:
                advice.append("Humidity is high, so prefer morning/evening sightseeing and carry water.")
        except Exception:
            pass

    # Month-specific generic advice
    if dates:
        advice.append(f"For {dates}, plan major outdoor sightseeing during comfortable daylight hours.")

    return advice


def weather_agent(state: dict) -> dict:
    print("running weather agent")

    place = state.get("trip_place", "")
    dates = state.get("trip_dates", "Not specified")

    warnings = state.setdefault("warnings", [])
    trace = state.setdefault("trace", [])

    if not place:
        state["weather_info"] = "Weather information not available because destination is missing."
        state["best_time"] = "Best-time information not available."

        warnings.append("Destination missing. Could not fetch weather.")

        trace.append({
            "step": "Weather",
            "source": "OpenWeather + Serper",
            "output": "Destination missing"
        })

        return state

    # 1. Live current conditions from OpenWeather
    live = get_weather(place)

    live_txt = ""

    if isinstance(live, dict) and "error" not in live:
        temp = live.get("temp_celsius", "N/A")
        description = live.get("description", "N/A")
        humidity = live.get("humidity", "N/A")

        live_txt = (
            f"Current weather:\n"
            f"- Temperature: {temp}°C\n"
            f"- Condition: {description}\n"
            f"- Humidity: {humidity}%"
        )
    else:
        warnings.append(f"Could not fetch live weather for {place}.")

    # 2. Month outlook from Serper
    month_query = f"{place} weather in {dates} in Celsius travel outlook India"
    month_data = search_serper(month_query, num_results=3)
    month_txt = _first_snippet(month_data)

    # 3. Best time to visit from Serper
    best_time_query = f"best time to visit {place} weather Celsius"
    best_time_data = search_serper(best_time_query, num_results=3)
    best_time_txt = _first_snippet(best_time_data)

    # 4. Practical travel advice
    advice_list = build_weather_advice(place, dates, live, month_txt)

    # 5. Create clean formatted weather summary
    weather_summary_parts = []

    weather_summary_parts.append(f"Weather summary for {place}:")

    if live_txt:
        weather_summary_parts.append(live_txt)

    if month_txt:
        weather_summary_parts.append(
            f"Travel outlook for {dates}:\n{month_txt}"
        )

    if advice_list:
        advice_text = "Travel advice:\n"
        for advice in advice_list:
            advice_text += f"- {advice}\n"

        weather_summary_parts.append(advice_text.strip())

    weather_summary = "\n\n".join(weather_summary_parts).strip()

    if not weather_summary:
        weather_summary = "Weather information not available."

    state["weather_info"] = weather_summary
    state["best_time"] = best_time_txt or "Best-time information not available."
    state["warnings"] = warnings

    trace.append({
        "step": "Weather + best time",
        "source": "OpenWeather + Serper",
        "queries": {
            "month_weather_query": month_query,
            "best_time_query": best_time_query
        },
        "output": {
            "weather": weather_summary,
            "best_time": state["best_time"]
        },
    })

    print("===== WEATHER STATE UPDATED =====")
    print(state["weather_info"])

    return state


# """
# Weather agent — fetches the month's weather + the best time to visit.
# Uses OpenWeather (live current conditions) + Serper search (month outlook and
# best time). No LLM call here, to save quota.
# """
 
# from services.weather_service import get_weather
# from services.serper_service import search_serper
 
 
# def _first_snippet(data: dict) -> str:
#     if not isinstance(data, dict) or "error" in data:
#         return ""
#     ab = data.get("answerBox") or {}
#     if ab.get("answer"):
#         return ab["answer"]
#     if ab.get("snippet"):
#         return ab["snippet"]
#     org = data.get("organic") or []
#     if org:
#         return org[0].get("snippet", "")
#     return ""
 
 
# def weather_agent(state: dict) -> dict:
#     print("running weather agent")
#     place = state.get("trip_place", "")
#     dates = state.get("trip_dates", "")
#     warnings = state.get("warnings", [])
 
#     # Live current conditions
#     live = get_weather(place) if place else {"error": "no place"}
#     if isinstance(live, dict) and "error" not in live:
#         live_txt = (f"Currently {live['temp_celsius']}°C, {live['description']}, "
#                     f"humidity {live['humidity']}%.")
#     else:
#         live_txt = ""
#         warnings.append(f"Could not fetch live weather for {place}.")
 
#     # Month outlook + best time to visit (Serper)
#     month_txt = _first_snippet(search_serper(f"{place} weather in {dates}", num_results=3)) if place else ""
#     best = _first_snippet(search_serper(f"best time to visit {place}", num_results=3)) if place else ""
 
#     summary_bits = []
#     if live_txt:
#         summary_bits.append(live_txt)
#     if month_txt:
#         summary_bits.append(f"Outlook for {dates}: {month_txt}")
#     weather_summary = " ".join(summary_bits) or "Weather information not available."
 
#     state["weather_info"] = weather_summary
#     state["best_time"] = best or "Best-time information not available."
#     state["warnings"] = warnings
 
#     state.setdefault("trace", []).append({
#         "step": "Weather + best time",
#         "source": "OpenWeather + Serper",
#         "output": {"weather": weather_summary, "best_time": state["best_time"]},
#     })
#     return state
 
 


# code using openmeteo api
# from services.weather_service import get_weather, get_climate_summary
# from services.llm import call_gemini, llm_enabled


# def extract_month(dates: str) -> str:
#     if not dates:
#         return ""
#     try:
#         return dates.split("-")[1]   # "2026-07-10" -> "07"
#     except:
#         return ""


# def weather_agent(state: dict) -> dict:
#     print("running weather agent")

#     place = (state.get("trip_place") or "").strip()
#     dates = (state.get("trip_dates") or "").strip()
#     warnings = state.get("warnings", [])

#     if not place:
#         state["weather_info"] = "Weather information not available."
#         state["best_time"] = "Best-time not available."
#         state["warnings"] = warnings
#         return state

#     # ✅ 1. CURRENT WEATHER
#     live = get_weather(place)
#     live_txt = ""

#     if "error" not in live:
#         wind_val = live.get("wind_kmh")
#         wind = f", wind {wind_val} km/h" if wind_val else ""

#         live_txt = (
#             f"Currently {live.get('temp_celsius')}°C with {live.get('description').lower()}, "
#             f"humidity around {live.get('humidity')}%{wind}."
#         )
#     else:
#         warnings.append(f"Weather failed: {live.get('error')}")

#     # ✅ 2. CLIMATE SUMMARY (FIXED KEYS)
#     month_value = extract_month(dates)
#     climate = get_climate_summary(place, month=month_value)

#     month_txt = ""
#     best_txt = ""

#     if "error" not in climate:

#         # ✅ Travel condition explanation
#         month_txt = climate.get("travel_month_summary", "")

#         # ✅ FIX: correct key
#         best_txt = climate.get("best_time_text", "")

#     else:
#         warnings.append(f"Climate failed: {climate.get('error')}")

#     # ✅ 3. LLM fallback (only if everything failed)
#     if not live_txt and not month_txt:
#         if llm_enabled():
#             prompt = (
#                 f"Give a short travel weather summary for {place}"
#                 + (f" in {dates}" if dates else "")
#                 + ". Include temperature, weather condition and best time."
#             )

#             llm_out = call_gemini(prompt)

#             if llm_out:
#                 state["weather_info"] = llm_out
#                 state["best_time"] = "AI generated estimate"
#                 return state

#     # ✅ 4. FINAL ELABORATED OUTPUT
#     final_weather = f"""
# 🌤 Weather Overview:
# {live_txt}

# 📊 Travel Conditions:
# {month_txt or "General weather conditions vary."}

# 📅 Best Time to Visit:
# {best_txt or "Weather varies throughout the year."}
# """

#     state["weather_info"] = final_weather.strip()
#     state["best_time"] = best_txt or "Not available"
#     state["warnings"] = warnings

#     return state
