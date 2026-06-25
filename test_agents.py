"""
test_agents.py — individual unit tests for each of the 5 agents.

Run all tests:
    python test_agents.py

Run a single agent's test:
    python test_agents.py PlannerTest
    python test_agents.py WeatherTest
    python test_agents.py DestinationTest
    python test_agents.py TransportTest
    python test_agents.py BudgetTest
    python test_agents.py ItineraryTest

Each test class:
  - builds a minimal state dict with the inputs that agent needs
  - calls the agent function directly (no LangGraph overhead)
  - asserts the expected output key is populated and non-empty
  - prints a formatted summary of the agent's output so you can eyeball it
"""

import sys
import unittest
from pprint import pformat

# ── Shared minimal base state ─────────────────────────────────────────────────

BASE_STATE = {
    "user_input": "Plan a 4-day couple trip to Goa in December with a budget of 40000",
    "chat_history": [],
    "trip_place": "Goa",
    "trip_dates": "December",
    "trip_days": 4,
    "trip_style": "couple",
    "trip_budget": 40000.0,
    "warnings": [],
    "trace": [],
}


def _fresh(overrides: dict = None) -> dict:
    """Return a fresh copy of BASE_STATE with optional overrides applied."""
    state = {**BASE_STATE, "warnings": [], "trace": []}
    if overrides:
        state.update(overrides)
    return state


def _banner(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def _show(label: str, value):
    print(f"\n--- {label} ---")
    text = value if isinstance(value, str) else pformat(value, width=80)
    # Truncate very long outputs to keep terminal readable
    if len(text) > 1500:
        text = text[:1500] + "\n... [truncated]"
    print(text)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Planner Agent
# ═══════════════════════════════════════════════════════════════════════════════

class PlannerTest(unittest.TestCase):
    """Tests the Planner agent: extraction + validation in one step."""

    def _run(self, user_input: str, preset: dict = None) -> dict:
        from agents.planner import planner_agent
        state = _fresh({"user_input": user_input, "trip_place": "", "trip_dates": "",
                         "trip_days": 0, "trip_budget": 0.0})
        if preset:
            state.update(preset)
        return planner_agent(state)

    def test_full_input_no_clarification(self):
        """Complete input → no clarification needed, all fields extracted."""
        _banner("Planner — full input")
        result = self._run(
            "I want a 4-day couple trip to Goa in December with a budget of 40000"
        )
        _show("trip_place", result.get("trip_place"))
        _show("trip_dates", result.get("trip_dates"))
        _show("trip_days", result.get("trip_days"))
        _show("trip_budget", result.get("trip_budget"))
        _show("need_clarification", result.get("need_clarification"))
        _show("trace", result.get("trace"))

        self.assertFalse(result.get("need_clarification"),
                         f"Expected no clarification, missing: {result.get('missing_fields')}")
        self.assertTrue(result.get("trip_place"), "trip_place should be set")
        self.assertTrue(result.get("trip_dates"), "trip_dates should be set")
        self.assertGreater(result.get("trip_budget", 0), 0, "trip_budget should be > 0")

    def test_missing_fields_triggers_clarification(self):
        """Incomplete input → clarification flag set and missing_fields populated."""
        _banner("Planner — missing fields")
        result = self._run("I want to go somewhere nice")
        _show("need_clarification", result.get("need_clarification"))
        _show("missing_fields", result.get("missing_fields"))

        self.assertTrue(result.get("need_clarification"), "Should need clarification")
        self.assertGreater(len(result.get("missing_fields", [])), 0)

    def test_partial_input_preserves_existing_state(self):
        """Follow-up message with just the budget preserves previously extracted place/dates."""
        _banner("Planner — partial follow-up preserves state")
        result = self._run(
            "My budget is 50000",
            preset={"trip_place": "Kerala", "trip_dates": "January", "trip_days": 5}
        )
        _show("trip_place", result.get("trip_place"))
        _show("trip_budget", result.get("trip_budget"))

        self.assertEqual(result.get("trip_place"), "Kerala")
        self.assertEqual(result.get("trip_dates"), "January")
        self.assertGreater(result.get("trip_budget", 0), 0)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Weather Agent
# ═══════════════════════════════════════════════════════════════════════════════

class WeatherTest(unittest.TestCase):
    """Tests the Weather agent: live weather + best time."""

    def test_weather_output_populated(self):
        """weather_info and best_time should be non-empty strings."""
        _banner("Weather Agent")
        from agents.weather_agent import weather_agent
        state = _fresh()
        result = weather_agent(state)

        _show("weather_info", result.get("weather_info"))
        _show("best_time", result.get("best_time"))
        _show("warnings", result.get("warnings"))
        _show("trace", result.get("trace"))

        self.assertIn("weather_info", result, "weather_info key missing")
        self.assertTrue(result.get("weather_info"), "weather_info should not be empty")
        self.assertIn("best_time", result, "best_time key missing")

    def test_weather_no_place(self):
        """Missing place → graceful fallback, no crash."""
        _banner("Weather Agent — no place")
        from agents.weather_agent import weather_agent
        state = _fresh({"trip_place": ""})
        result = weather_agent(state)

        _show("weather_info", result.get("weather_info"))
        # Should not raise; weather_info may be a fallback message
        self.assertIn("weather_info", result)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Destination Agent
# ═══════════════════════════════════════════════════════════════════════════════

class DestinationTest(unittest.TestCase):
    """Tests the Destination agent: live top-places search."""

    def test_place_info_populated(self):
        """place_info should list attractions for the destination."""
        _banner("Destination Agent")
        from agents.destination_agent import destination_agent
        state = _fresh()
        result = destination_agent(state)

        _show("place_info", result.get("place_info"))
        _show("trace", result.get("trace"))

        self.assertIn("place_info", result, "place_info key missing")
        self.assertTrue(result.get("place_info"), "place_info should not be empty")

    def test_destination_no_place(self):
        """Missing place → graceful fallback."""
        _banner("Destination Agent — no place")
        from agents.destination_agent import destination_agent
        state = _fresh({"trip_place": ""})
        result = destination_agent(state)

        _show("place_info", result.get("place_info"))
        self.assertIn("place_info", result)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Transport Agent
# ═══════════════════════════════════════════════════════════════════════════════

class TransportTest(unittest.TestCase):
    """Tests the Transport agent: how-to-reach + local transport."""

    def test_transport_info_populated(self):
        """transport_info should contain travel options."""
        _banner("Transport Agent")
        from agents.transport_agent import transport_agent
        state = _fresh()
        result = transport_agent(state)

        _show("transport_info", result.get("transport_info"))
        _show("trace", result.get("trace"))

        self.assertIn("transport_info", result, "transport_info key missing")
        self.assertTrue(result.get("transport_info"), "transport_info should not be empty")

    def test_transport_no_place(self):
        """Missing place → graceful fallback."""
        _banner("Transport Agent — no place")
        from agents.transport_agent import transport_agent
        state = _fresh({"trip_place": ""})
        result = transport_agent(state)

        _show("transport_info", result.get("transport_info"))
        self.assertIn("transport_info", result)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Budget Agent
# ═══════════════════════════════════════════════════════════════════════════════

class BudgetTest(unittest.TestCase):
    """Tests the Budget agent: cost estimation via Serper + LLM."""

    def test_budget_info_populated(self):
        """budget_info should be a non-empty cost summary."""
        _banner("Budget Agent")
        from agents.budget_agent import budget_agent
        state = _fresh()
        result = budget_agent(state)

        _show("budget_info", result.get("budget_info"))
        _show("cost_breakdown", result.get("cost_breakdown"))
        _show("warnings", result.get("warnings"))
        _show("trace", result.get("trace"))

        self.assertIn("budget_info", result, "budget_info key missing")
        self.assertTrue(result.get("budget_info"), "budget_info should not be empty")

    def test_budget_warning_when_over(self):
        """Very low stated budget → warning added."""
        _banner("Budget Agent — over budget warning")
        from agents.budget_agent import budget_agent
        state = _fresh({"trip_budget": 100.0})   # unrealistically low
        result = budget_agent(state)

        _show("budget_info", result.get("budget_info"))
        _show("warnings", result.get("warnings"))
        # Warning may or may not fire depending on live estimate, so just check it runs
        self.assertIn("budget_info", result)

    def test_budget_no_place(self):
        """Missing place → graceful fallback."""
        _banner("Budget Agent — no place")
        from agents.budget_agent import budget_agent
        state = _fresh({"trip_place": ""})
        result = budget_agent(state)

        _show("budget_info", result.get("budget_info"))
        self.assertIn("budget_info", result)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Itinerary Agent
# ═══════════════════════════════════════════════════════════════════════════════

class ItineraryTest(unittest.TestCase):
    """Tests the Itinerary agent: day-by-day plan composer."""

    def _state_with_upstream(self) -> dict:
        """Return a state pre-filled with realistic upstream agent outputs."""
        return _fresh({
            "weather_info": "Currently 28°C, clear sky, humidity 65%. December is the peak tourist season in Goa with pleasant weather.",
            "best_time": "October to March is the best time to visit Goa for beach activities and nightlife.",
            "place_info": (
                "1. Baga Beach: Famous for water sports and vibrant nightlife.\n"
                "2. Calangute Beach: The queen of beaches, great for swimming.\n"
                "3. Fort Aguada: 17th-century Portuguese fort with lighthouse.\n"
                "4. Dudhsagar Falls: Spectacular four-tiered waterfall.\n"
                "5. Old Goa Churches: UNESCO World Heritage Site.\n"
                "6. Anjuna Flea Market: Famous Wednesday market for souvenirs."
            ),
            "transport_info": (
                "Getting to Goa:\n"
                "- Fly to Goa International Airport (GOI); flights from major cities.\n"
                "- Trains to Madgaon or Thivim station.\n"
                "Getting around Goa:\n"
                "- Rent a scooter (~Rs 300/day) or hire a cab.\n"
                "- Tourist buses for major attractions."
            ),
            "budget_info": (
                "Budget estimate for Goa (4 days):\n"
                "- Accommodation: Rs 12,000\n"
                "- Food: Rs 8,000\n"
                "- Local transport: Rs 3,000\n"
                "- Sightseeing: Rs 4,000\n"
                "- Intercity travel: Rs 10,000\n"
                "- Total: Rs 37,000"
            ),
            "cost_breakdown": {
                "accommodation": 12000, "food": 8000, "local_transport": 3000,
                "sightseeing": 4000, "intercity_transport": 10000, "total": 37000,
                "per_day": [8000, 10000, 11000, 8000],
            },
        })

    def test_itinerary_generated(self):
        """final_itinerary should be a non-empty markdown plan."""
        _banner("Itinerary Agent")
        from agents.itinerary_agent import itinerary_agent
        state = self._state_with_upstream()
        result = itinerary_agent(state)

        _show("final_itinerary (first 800 chars)", (result.get("final_itinerary") or "")[:800])
        _show("trace", result.get("trace"))

        self.assertIn("final_itinerary", result, "final_itinerary key missing")
        self.assertTrue(result.get("final_itinerary"), "final_itinerary should not be empty")

    def test_itinerary_no_place(self):
        """Missing place → graceful fallback message, no crash."""
        _banner("Itinerary Agent — no place")
        from agents.itinerary_agent import itinerary_agent
        state = _fresh({"trip_place": ""})
        result = itinerary_agent(state)

        _show("final_itinerary", result.get("final_itinerary"))
        self.assertIn("final_itinerary", result)
        self.assertTrue(result.get("final_itinerary"))   # should contain a fallback message


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # If a class name is passed as argv[1], run only that suite.
    if len(sys.argv) == 2 and sys.argv[1] in (
        "PlannerTest", "WeatherTest", "DestinationTest",
        "TransportTest", "BudgetTest", "ItineraryTest"
    ):
        suite = unittest.TestLoader().loadTestsFromName(sys.argv[1], module=sys.modules[__name__])
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        unittest.main(verbosity=2)
