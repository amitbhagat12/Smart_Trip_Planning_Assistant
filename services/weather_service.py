import requests
import os
from dotenv import load_dotenv
 
load_dotenv()
 
def get_weather(city: str) -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
   
    try:
        response = requests.get(url)
        data= response.json()
       
        if data.get("cod") != 200:
            return {"error": data.get("message", "An error occurred while fetching weather data.")}
       
        return {
            "city": city,
            "temp_celsius": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }
    except Exception as e:
        return {"error": str(e)}
 



# """
# weather_service.py

# ✅ Open-Meteo + ERA5 (stable + no API key)
# ✅ Now with smart interpretation layer (more elaborated answers)

# """

# import requests
# from datetime import date

# # ✅ FIXED URLs
# OPEN_METEO_GEO  = "https://geocoding-api.open-meteo.com/v1/search"
# OPEN_METEO_NOW  = "https://api.open-meteo.com/v1/forecast"
# OPEN_METEO_HIST = "https://archive-api.open-meteo.com/v1/archive"

# TIMEOUT_FAST = 5
# TIMEOUT_HIST = 10

# _geocode_cache = {}

# WMO_CODES = {
#     0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
#     61: "Light rain", 63: "Rain", 65: "Heavy rain",
#     80: "Showers", 81: "Moderate showers", 82: "Heavy showers",
#     95: "Thunderstorm"
# }

# MONTH_NAMES = [
#     "", "January", "February", "March", "April", "May", "June",
#     "July", "August", "September", "October", "November", "December",
# ]


# # ✅ CURRENT WEATHER
# def get_weather(city: str) -> dict:
#     coords = _geocode(city)
#     if "error" in coords:
#         return coords

#     try:
#         r = requests.get(
#             OPEN_METEO_NOW,
#             params={
#                 "latitude": coords["lat"],
#                 "longitude": coords["lon"],
#                 "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
#                 "timezone": "auto",
#             },
#             timeout=TIMEOUT_FAST
#         )
#         r.raise_for_status()

#         cur = r.json().get("current", {})
#         code = cur.get("weather_code")

#         return {
#             "temp_celsius": cur.get("temperature_2m"),
#             "description": WMO_CODES.get(code, f"Code {code}"),
#             "humidity": cur.get("relative_humidity_2m"),
#             "wind_kmh": cur.get("wind_speed_10m"),
#         }

#     except Exception as e:
#         return {"error": str(e)}


# # ✅ CLIMATE LOGIC (IMPROVED)
# def get_climate_summary(city: str, month: str = "") -> dict:
#     coords = _geocode(city)
#     if "error" in coords:
#         return coords

#     end_year = date.today().year - 1
#     start_year = end_year - 4

#     try:
#         r = requests.get(
#             OPEN_METEO_HIST,
#             params={
#                 "latitude": coords["lat"],
#                 "longitude": coords["lon"],
#                 "start_date": f"{start_year}-01-01",
#                 "end_date": f"{end_year}-12-31",
#                 "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
#                 "timezone": "auto",
#             },
#             timeout=TIMEOUT_HIST
#         )
#         r.raise_for_status()
#         data = r.json()

#     except Exception as e:
#         return {"error": str(e)}

#     daily = data.get("daily", {})
#     times = daily.get("time", [])
#     max_t = daily.get("temperature_2m_max", [])
#     min_t = daily.get("temperature_2m_min", [])
#     rain = daily.get("precipitation_sum", [])

#     acc = {m: {"max": [], "min": [], "rain": []} for m in range(1, 13)}

#     for i, t in enumerate(times):
#         try:
#             m = int(t.split("-")[1])
#             if max_t[i] is not None:
#                 acc[m]["max"].append(max_t[i])
#             if min_t[i] is not None:
#                 acc[m]["min"].append(min_t[i])
#             if rain[i] is not None:
#                 acc[m]["rain"].append(rain[i])
#         except:
#             continue

#     monthly_avg = {}
#     for m in range(1, 13):
#         d = acc[m]
#         monthly_avg[m] = {
#             "max": round(sum(d["max"]) / len(d["max"]), 1) if d["max"] else None,
#             "min": round(sum(d["min"]) / len(d["min"]), 1) if d["min"] else None,
#             "rain": round(sum(d["rain"]) / len(d["rain"]), 1) if d["rain"] else None,
#         }

#     # ✅ SMART INTERPRETATION
#     good_months = []
#     avoid_months = []

#     for m, v in monthly_avg.items():
#         if v["max"] is None:
#             continue

#         temp = v["max"]
#         rain_val = v["rain"] or 0

#         if 20 <= temp <= 32 and rain_val < 5:
#             good_months.append(MONTH_NAMES[m])
#         elif rain_val > 10:
#             avoid_months.append(MONTH_NAMES[m])

#     # ✅ MONTH-SPECIFIC SUMMARY
#     month_summary = ""
#     if month:
#         try:
#             m = int(month)
#             v = monthly_avg.get(m)

#             if v and v["max"] is not None:
#                 month_summary = (
#                     f"{MONTH_NAMES[m]} typically has temperatures around "
#                     f"{v['min']}–{v['max']}°C with average rainfall of {v['rain']} mm."
#                 )
#         except:
#             pass

#     # ✅ FINAL ELABORATED OUTPUT
#     best_text = ""

#     if good_months:
#         best_text += f"Best time to visit: {', '.join(good_months)}. "

#     if avoid_months:
#         best_text += f"Avoid months like {', '.join(avoid_months)} due to heavy rainfall."

#     if not best_text:
#         best_text = "Weather conditions vary across the year."

#     return {
#         "travel_month_summary": month_summary,
#         "best_time_text": best_text,
#     }


# # ✅ GEOCODE
# def _geocode(city: str) -> dict:
#     key = city.lower().strip()

#     if key in _geocode_cache:
#         return _geocode_cache[key]

#     try:
#         r = requests.get(
#             OPEN_METEO_GEO,
#             params={"name": city, "count": 1},
#             timeout=TIMEOUT_FAST
#         )
#         r.raise_for_status()

#         data = r.json().get("results", [])

#         if not data:
#             return {"error": "City not found"}

#         coords = {
#             "lat": data[0]["latitude"],
#             "lon": data[0]["longitude"]
#         }

#         _geocode_cache[key] = coords
#         return coords

#     except Exception as e:
#         return {"error": str(e)}


# code using weatherapi
# """
# weather_service.py

# ✅ Primary: WeatherAPI
# ✅ Fallback: Gemini (LLM)
# ✅ Returns structured + elaborated data

# """

# import os
# import requests
# from dotenv import load_dotenv

# from services.llm import call_gemini, llm_enabled

# load_dotenv()

# API_KEY = os.getenv("WEATHER_API_KEY")
# BASE_URL = "http://api.weatherapi.com/v1/forecast.json"


# def get_weather(city: str) -> dict:
#     """
#     Returns:
#     {
#         temp_celsius,
#         description,
#         humidity,
#         wind_kmh,
#         travel_summary,
#         best_time_text
#     }
#     """

#     # ✅ STEP 1: WeatherAPI
#     if API_KEY:
#         try:
#             params = {
#                 "key": API_KEY,
#                 "q": city,
#                 "days": 7,
#                 "aqi": "no"
#             }

#             r = requests.get(BASE_URL, params=params, timeout=5)
#             r.raise_for_status()
#             data = r.json()

#             current = data.get("current", {})
#             forecast_days = data.get("forecast", {}).get("forecastday", [])

#             temp = current.get("temp_c")
#             condition = current.get("condition", {}).get("text", "")
#             humidity = current.get("humidity")
#             wind = current.get("wind_kph")

#             # ✅ Calculate averages
#             max_temps, min_temps, rain = [], [], []

#             for d in forecast_days:
#                 day = d.get("day", {})
#                 max_temps.append(day.get("maxtemp_c", 0))
#                 min_temps.append(day.get("mintemp_c", 0))
#                 rain.append(day.get("totalprecip_mm", 0))

#             avg_max = sum(max_temps) / len(max_temps) if max_temps else None
#             avg_min = sum(min_temps) / len(min_temps) if min_temps else None
#             avg_rain = sum(rain) / len(rain) if rain else None

#             # ✅ Smart travel logic
#             if avg_max is None:
#                 best = "Best-time not available."
#             elif avg_max <= 30 and avg_rain < 5:
#                 best = "Excellent time to visit."
#             elif avg_max <= 34:
#                 best = "Good time to visit."
#             elif avg_rain > 10:
#                 best = "Rainy period — expect frequent showers."
#             else:
#                 best = "Hot weather — plan outdoor activities carefully."

#             travel_summary = (
#                 f"Expected temperature {round(avg_min,1)}–{round(avg_max,1)}°C "
#                 f"with average rainfall {round(avg_rain,1)} mm."
#                 if avg_max is not None else ""
#             )

#             return {
#                 "temp_celsius": temp,
#                 "description": condition,
#                 "humidity": humidity,
#                 "wind_kmh": wind,
#                 "travel_summary": travel_summary,
#                 "best_time_text": best,
#                 "source": "weatherapi"
#             }

#         except Exception as e:
#             api_error = str(e)
#     else:
#         api_error = "Missing WEATHER_API_KEY"

#     # ✅ STEP 2: Gemini fallback
#     if llm_enabled():
#         try:
#             prompt = f"""
# Give a concise but helpful weather summary for traveling to {city}.
# Include:
# - current-like conditions
# - temperature range
# - best time to visit
# Keep under 80 words.
# """

#             response = call_gemini(prompt)

#             return {
#                 "temp_celsius": None,
#                 "description": "AI-generated summary",
#                 "humidity": None,
#                 "wind_kmh": None,
#                 "travel_summary": response,
#                 "best_time_text": "Generated using AI estimate",
#                 "source": "gemini_fallback"
#             }

#         except Exception as e:
#             return {"error": f"Both WeatherAPI & Gemini failed: {str(e)}"}

#     return {"error": f"WeatherAPI failed: {api_error}"}


# # ✅ Compatibility wrapper
# def get_climate_summary(city: str, month: str = "") -> dict:
#     data = get_weather(city)

#     if "error" in data:
#         return data

#     return {
#         "travel_month_summary": data.get("travel_summary", ""),
#         "best_time_text": data.get("best_time_text", "")
#     }

