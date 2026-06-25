# """
# Replanning logic for Smart Trip Planner.

# Determines which agents need to re-run when the user changes trip parameters,
# instead of blindly re-running all agents every time.

# Dependency map (what each agent needs from state):
#   weather    → trip_place, trip_dates
#   destination → trip_place, trip_days, trip_style, trip_dates
#   transport   → trip_place
#   budget      → trip_place, trip_days, trip_budget
#   itinerary   → ALL (composes everything from other agents)

# Rules:
#   - If destination (trip_place) changes → re-run ALL agents (everything is place-specific)
#   - If dates (trip_dates) changes       → re-run weather, destination, itinerary
#   - If days (trip_days) changes         → re-run destination, budget, itinerary
#   - If budget (trip_budget) changes     → re-run budget, itinerary (NOT weather/transport/destination)
#   - If style (trip_style) changes       → re-run destination, itinerary
#   - itinerary always re-runs if ANY other agent ran (it composes everything)
# """

# from typing import Set


# # Maps each changed field → which agents must re-run
# FIELD_AGENT_MAP = {
#     "trip_place":  {"weather", "destination", "transport", "budget", "itinerary"},
#     "trip_dates":  {"weather", "destination", "itinerary"},
#     "trip_days":   {"destination", "budget", "itinerary"},
#     "trip_budget": {"budget", "itinerary"},
#     "trip_style":  {"destination", "itinerary"},
# }

# ALL_AGENTS = ["weather", "destination", "transport", "budget", "itinerary"]


# def detect_changed_fields(prev_state: dict, new_state: dict) -> Set[str]:
#     """
#     Compare previous and new state to find which trip parameters changed.
#     Returns a set of field names that changed.
#     """
#     tracked_fields = list(FIELD_AGENT_MAP.keys())
#     changed = set()

#     for field in tracked_fields:
#         old_val = prev_state.get(field)
#         new_val = new_state.get(field)

#         # Normalise for comparison
#         if isinstance(old_val, str):
#             old_val = old_val.strip().lower()
#         if isinstance(new_val, str):
#             new_val = new_val.strip().lower()

#         if old_val != new_val:
#             # Only flag as changed if the new value is actually set
#             if new_val:
#                 changed.add(field)

#     return changed


# def agents_to_run(changed_fields: Set[str], is_first_run: bool) -> list:
#     """
#     Returns the ordered list of agents that need to re-run.
#     Preserves the natural execution order:
#       weather → destination → transport → budget → itinerary
#     """
#     if is_first_run or not changed_fields:
#         # First run or no changes detected → run everything
#         return ALL_AGENTS

#     needed: Set[str] = set()
#     for field in changed_fields:
#         needed |= FIELD_AGENT_MAP.get(field, set())

#     # Always add itinerary if anything else needs to run
#     # (itinerary composes from all other agent outputs)
#     if needed - {"itinerary"}:
#         needed.add("itinerary")

#     # Return in fixed pipeline order
#     return [a for a in ALL_AGENTS if a in needed]


# def describe_replan(changed_fields: Set[str], agents: list) -> str:
#     """Human-readable explanation of what changed and what will re-run."""
#     if not changed_fields:
#         return "No changes detected — skipping all agents."

#     field_labels = {
#         "trip_place":  "destination",
#         "trip_dates":  "travel dates",
#         "trip_days":   "trip duration",
#         "trip_budget": "budget",
#         "trip_style":  "trip style",
#     }
#     changed_readable = [field_labels.get(f, f) for f in changed_fields]
#     skipped = [a for a in ALL_AGENTS if a not in agents]

#     msg = f"Changed: {', '.join(changed_readable)}. "
#     msg += f"Re-running: {', '.join(agents)}."
#     if skipped:
#         msg += f" Skipping (using cached): {', '.join(skipped)}."
#     return msg

from typing import Set

FIELD_AGENT_MAP = {
    "trip_place":  {"weather", "destination", "transport", "budget", "itinerary"},
    "trip_dates":  {"weather", "destination", "itinerary"},
    "trip_days":   {"destination", "budget", "itinerary"},
    "trip_budget": {"budget", "itinerary"},
    "trip_style":  {"destination", "itinerary"},
}

ALL_AGENTS = ["weather", "destination", "transport", "budget", "itinerary"]


def detect_changed_fields(prev_state: dict, new_state: dict) -> Set[str]:
    changed = set()

    for field in FIELD_AGENT_MAP.keys():
        old_val = prev_state.get(field)
        new_val = new_state.get(field)

        if isinstance(old_val, str):
            old_val = old_val.strip().lower()
        if isinstance(new_val, str):
            new_val = new_val.strip().lower()

        if old_val != new_val:
            # ✅ FIX: allow 0 / empty values
            if new_val is not None:
                changed.add(field)

    return changed


def agents_to_run(changed_fields: Set[str], is_first_run: bool) -> list:
    if is_first_run:
        return ALL_AGENTS

    if not changed_fields:
        return []

    needed = set()
    for field in changed_fields:
        needed |= FIELD_AGENT_MAP.get(field, set())

    if needed - {"itinerary"}:
        needed.add("itinerary")

    return [a for a in ALL_AGENTS if a in needed]


def describe_replan(changed_fields: Set[str], agents: list) -> str:
    if not changed_fields:
        return "No changes detected — skipping all agents."

    field_labels = {
        "trip_place":  "destination",
        "trip_dates":  "travel dates",
        "trip_days":   "trip duration",
        "trip_budget": "budget",
        "trip_style":  "trip style",
    }

    changed_readable = [field_labels.get(f, f) for f in changed_fields]
    skipped = [a for a in ALL_AGENTS if a not in agents]

    msg = f"Changed: {', '.join(changed_readable)}. "
    msg += f"Re-running: {', '.join(agents)}."
    if skipped:
        msg += f" Skipping: {', '.join(skipped)}."
    return msg