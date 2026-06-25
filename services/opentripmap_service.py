import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENTRIPMAP_API_KEY = os.getenv("OPENTRIPMAP_API_KEY")

BASE_URL = "https://api.opentripmap.com/0.1/en/places"


def opentripmap_enabled() -> bool:
    return bool(OPENTRIPMAP_API_KEY)


def _safe_get(url: str, params: dict):
    """
    Safely calls OpenTripMap API.
    Returns dict/list depending on API response.
    """
    if not OPENTRIPMAP_API_KEY:
        return {"error": "OPENTRIPMAP_API_KEY missing"}

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("OpenTripMap API error:", e)
        return {"error": str(e)}


def get_coordinates(place_name: str) -> dict:
    """
    Converts destination name into latitude and longitude.
    Example: Goa -> lat/lon
    """
    url = f"{BASE_URL}/geoname"

    params = {
        "name": place_name,
        "apikey": OPENTRIPMAP_API_KEY,
    }

    data = _safe_get(url, params)

    if isinstance(data, dict) and "error" in data:
        return data

    lat = data.get("lat")
    lon = data.get("lon")

    if lat is None or lon is None:
        return {"error": f"Could not find coordinates for {place_name}"}

    return {
        "name": data.get("name", place_name),
        "lat": lat,
        "lon": lon,
        "country": data.get("country"),
    }


def get_places_by_kinds(
    lat: float,
    lon: float,
    kinds: str,
    radius_m: int = 50000,
    limit: int = 30,
    rate=None
) -> list:
    """
    Fetches places near coordinates for specific kinds/categories.

    Important:
    For beaches, we do NOT force rate=2 because many beaches may not have
    rich descriptions in OpenTripMap.
    """
    url = f"{BASE_URL}/radius"

    params = {
        "radius": radius_m,
        "lat": lat,
        "lon": lon,
        "format": "json",
        "limit": limit,
        "kinds": kinds,
        "apikey": OPENTRIPMAP_API_KEY,
    }

    if rate is not None:
        params["rate"] = rate

    data = _safe_get(url, params)

    if isinstance(data, dict) and "error" in data:
        return []

    if not isinstance(data, list):
        return []

    return data


def get_place_details(xid: str) -> dict:
    """
    Gets full details of one place using xid.
    """
    if not xid:
        return {}

    url = f"{BASE_URL}/xid/{xid}"

    params = {
        "apikey": OPENTRIPMAP_API_KEY,
    }

    data = _safe_get(url, params)

    if isinstance(data, dict) and "error" in data:
        return {}

    return data


def clean_description(details: dict) -> str:
    """
    Extracts readable description from OpenTripMap details.
    """
    if not details:
        return ""

    wiki_extracts = details.get("wikipedia_extracts", {})

    if isinstance(wiki_extracts, dict):
        text = wiki_extracts.get("text", "")
        if text:
            return text.strip()

    info = details.get("info", {})

    if isinstance(info, dict):
        descr = info.get("descr", "")
        if descr:
            return descr.strip()

    return ""


def is_bad_category(kinds: str) -> bool:
    """
    Removes categories that are not useful for a tourist destination list.
    """
    if not kinds:
        return False

    lower_kinds = kinds.lower()

    blocked_categories = [
        "cinemas",
        "theatres",
        "theatres_and_entertainments",
        "banks",
        "shops",
        "industrial_facilities",
        "other",
        "unclassified_objects",
        "tourist_object",
        "adult",
        "casino",
    ]

    return any(category in lower_kinds for category in blocked_categories)


def category_score(kinds: str) -> int:
    """
    Gives higher ranking to tourist-relevant places.
    """
    if not kinds:
        return 0

    lower_kinds = kinds.lower()
    score = 0

    # Highest priority for beaches/nature in places like Goa
    if "beach" in lower_kinds or "beaches" in lower_kinds:
        score += 10

    if "natural" in lower_kinds:
        score += 7

    if "historic" in lower_kinds:
        score += 6

    if "architecture" in lower_kinds:
        score += 5

    if "cultural" in lower_kinds:
        score += 4

    if "museums" in lower_kinds:
        score += 3

    if "religion" in lower_kinds:
        score += 1

    return score


def get_destination_places(place_name: str, limit: int = 8, radius_m: int = 150000) -> dict:
    """
    Main function for destination agent.

    Improved for places like Goa:
    1. Searches beaches first.
    2. Uses larger radius.
    3. Does not force rate=2 for beaches.
    4. Filters bad categories.
    5. Prioritizes beaches, nature, historic and cultural places.
    """

    coordinates = get_coordinates(place_name)

    if "error" in coordinates:
        return {
            "error": coordinates["error"],
            "places": []
        }

    lat = coordinates["lat"]
    lon = coordinates["lon"]

    search_groups = [
        # Search beaches first
        {
            "kinds": "beaches",
            "rate": None,
            "priority": 30
        },
        {
            "kinds": "natural,beaches",
            "rate": None,
            "priority": 25
        },
        {
            "kinds": "water,beaches,natural",
            "rate": None,
            "priority": 20
        },
        {
            "kinds": "historic,architecture,fortifications",
            "rate": 1,
            "priority": 12
        },
        {
            "kinds": "cultural,museums,interesting_places",
            "rate": 1,
            "priority": 8
        },
        {
            "kinds": "natural,caves,waterfalls,gardens_and_parks",
            "rate": 1,
            "priority": 10
        },
    ]

    all_places = []
    seen_xids = set()
    seen_names = set()

    for group in search_groups:
        results = get_places_by_kinds(
            lat=lat,
            lon=lon,
            kinds=group["kinds"],
            radius_m=radius_m,
            limit=50,
            rate=group["rate"]
        )

        for item in results:
            name = item.get("name", "").strip()
            xid = item.get("xid", "")
            item_kinds = item.get("kinds", "")
            distance = item.get("dist", 999999)

            if not name or not xid:
                continue

            if xid in seen_xids:
                continue

            if name.lower() in seen_names:
                continue

            if is_bad_category(item_kinds):
                continue

            seen_xids.add(xid)
            seen_names.add(name.lower())

            score = group["priority"] + category_score(item_kinds)

            # Extra boost if actual name contains beach
            if "beach" in name.lower():
                score += 50

            # Extra boost if category contains beach
            if "beach" in item_kinds.lower() or "beaches" in item_kinds.lower():
                score += 40

            all_places.append({
                "name": name,
                "xid": xid,
                "kinds": item_kinds,
                "distance": distance,
                "score": score,
            })

    if not all_places:
        return {
            "error": f"No useful tourist places found for {place_name}",
            "coordinates": coordinates,
            "places": []
        }

    all_places = sorted(
        all_places,
        key=lambda x: (-x["score"], x["distance"])
    )

    final_places = []

    for place in all_places:
        details = get_place_details(place["xid"])

        description = clean_description(details)

        wikipedia_url = details.get("wikipedia", "")
        preview = details.get("preview", {})

        image = ""
        if isinstance(preview, dict):
            image = preview.get("source", "")

        final_places.append({
            "name": place["name"],
            "xid": place["xid"],
            "kinds": place["kinds"],
            "distance": place["distance"],
            "description": description,
            "wikipedia": wikipedia_url,
            "image": image,
            "score": place["score"],
        })

        if len(final_places) >= limit:
            break

    return {
        "coordinates": coordinates,
        "places": final_places
    }
