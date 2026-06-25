import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


def search_serper(query: str, num_results: int = 5) -> dict:
    """
    Calls Serper API and returns Google search results.
    """

    if not SERPER_API_KEY:
        return {
            "error": "SERPER_API_KEY not found in .env file"
        }

    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "q": query,
        "num": num_results
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        response.raise_for_status()
        return response.json()

    except Exception as e:
        return {
            "error": str(e)
        }