"""
Lightweight parsing helpers (used only as a fallback when the LLM extractor is
unavailable). These parse the user's own words — there is NO hard-coded list of
places or answers anywhere.
"""

import re

_MONTHS = ["january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december"]
_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def extract_place_from_input(text: str) -> str:
    """Pull a destination from phrasing like 'trip to X' / 'visit X' / bare 'X'."""
    not_place = set(_MONTHS) | {"couple", "family", "solo", "relaxed", "adventure",
                                "balanced", "friends", "group", "yes", "no"}
    m = re.search(r"\b(?:trip to|travel to|going to|go to|visiting|visit|holiday in|"
                  r"vacation in|to|in)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text, re.IGNORECASE)
    stop = {"for", "and", "in", "on", "with", "my", "the", "a", "an", "this",
            "next", "during", "over", "budget", "days", "day", "trip"}
    if m:
        words = [w for w in m.group(1).split()]
        while words and words[-1].lower() in stop:
            words.pop()
        cand = " ".join(words).lower()
        if words and cand not in not_place:
            return " ".join(w.capitalize() for w in words)
    # Bare reply like "Delhi"
    t = text.strip().lower()
    if 1 <= len(t.split()) <= 2 and re.fullmatch(r"[a-z ]+", t) and t not in not_place:
        return t.title()
    return ""


def extract_days_from_input(text: str) -> int:
    t = text.lower()
    m = re.search(r"(\d+)\s*[-\s]?\s*day", t)
    if m:
        return int(m.group(1))
    for word, num in _WORD_NUM.items():
        if word in t:
            return num
    return 0


def extract_budget_from_input(text: str) -> float:
    t = text.replace(",", "").lower()
    m = re.search(r"(\d+)\s*k\b", t)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r"(\d{4,7})", t)
    if m:
        return float(m.group(1))
    return 0.0


def extract_month_from_input(text: str) -> str:
    t = text.lower()
    for mon in _MONTHS:
        if mon in t:
            return mon.capitalize()
    return ""


def extract_style_from_input(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["couple", "honeymoon", "romantic"]):
        return "couple"
    if any(w in t for w in ["family", "kids", "children"]):
        return "family"
    if any(w in t for w in ["solo", "alone", "myself"]):
        return "solo"
    if any(w in t for w in ["friends", "group", "gang"]):
        return "friends group"
    return "general"
