import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Accept either name so existing .env files keep working.
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Configurable model (default to  widely-available one).
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# function to check if api key exists or not
def llm_enabled() -> bool:
    return bool(api_key)


# def call_gemini(prompt: str) -> str:
#     """Call Gemini and always return a string ('' on any failure)."""
#     if not api_key:
#         return ""
#     try:
#         print("=====GEMINI CALLED=====")
#         model = genai.GenerativeModel(MODEL)
#         resp = model.generate_content(prompt)
#         text = getattr(resp, "text", None)
#         if text:
#             return text.strip()
#         # Fallback: stitch candidate parts if .text is empty
#         parts = []
#         for c in getattr(resp, "candidates", []) or []:
#             for p in getattr(getattr(c, "content", None), "parts", []) or []:
#                 t = getattr(p, "text", "")
#                 if t:
#                     parts.append(t)
#         return "".join(parts).strip()
#     except Exception as e:
#         print("Gemini error:", e)
#         return ""

def call_gemini(prompt: str) -> str:
    """
    Call Gemini and always return a string.
    Also prints token usage if available.
    """

    if not api_key:
        print("Gemini API key missing.")
        return ""

    try:
        print("===== GEMINI CALLED =====")

        model = genai.GenerativeModel(MODEL)

        # Optional: count input prompt tokens before call
        try:
            prompt_tokens = model.count_tokens(prompt)
            print("Gemini input prompt tokens:", prompt_tokens.total_tokens)
        except Exception as token_error:
            print("Could not count prompt tokens before call:", token_error)

        resp = model.generate_content(prompt)

        # Print usage metadata after call
        usage = getattr(resp, "usage_metadata", None)

        if usage:
            prompt_token_count = getattr(usage, "prompt_token_count", None)
            candidates_token_count = getattr(usage, "candidates_token_count", None)
            total_token_count = getattr(usage, "total_token_count", None)

            print("===== GEMINI TOKEN USAGE =====")
            print("Prompt tokens:", prompt_token_count)
            print("Output tokens:", candidates_token_count)
            print("Total tokens:", total_token_count)
            print("==============================")
        else:
            print("Gemini token usage metadata not available.")

        text = getattr(resp, "text", None)

        if text:
            return text.strip()

        # Fallback: stitch candidate parts if resp.text is empty
        parts = []

        for candidate in getattr(resp, "candidates", []) or []:
            content = getattr(candidate, "content", None)

            for part in getattr(content, "parts", []) or []:
                part_text = getattr(part, "text", "")

                if part_text:
                    parts.append(part_text)

        return "".join(parts).strip()

    except Exception as e:
        print("Gemini error:", e)
        return ""


def extract_json(text: str):
    """Parse a JSON object/array from model output (handles ``` fences)."""
    if not text:
        return None
    t = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", t, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                return None
    return None
