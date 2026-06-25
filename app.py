# import streamlit as st
# from graph.workflow import invoke_smart

# st.set_page_config(
#     page_title="Smart Trip Planner",
#     page_icon="✈️",
#     layout="wide"
# )

# st.title("✈️ Smart Trip Planning Assistant")

# # ---------------- Session State ----------------
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# if "trip_state" not in st.session_state:
#     st.session_state.trip_state = {
#         "user_input": "",
#         "chat_history": [],
#         "trip_place": "",
#         "trip_dates": "",
#         "trip_days": 0,
#         "trip_style": "",
#         "trip_budget": 0.0,
#         "budget_preference": "",
#         "weather_info": "",
#         "best_time": "",
#         "place_info": "",
#         "transport_info": "",
#         "budget_info": "",
#         "cost_breakdown": {},
#         "final_itinerary": "",
#         "warnings": [],
#         "trace": [],
#         "need_clarification": False,
#         "missing_fields": [],
#         # Replan metadata (empty until first run)
#         "_replan_agents": [],
#         "_replan_message": "",
#         "_changed_fields": [],
#     }

# # ---------------- Sidebar ----------------
# with st.sidebar:
#     st.header("🔍 Agent Outputs")

#     state = st.session_state.trip_state

#     choice = st.selectbox(
#         "Select agent output:",
#         [
#             "Weather & best time",
#             "Destination",
#             "Transport",
#             "Budget",
#             "Final Itinerary",
#         ],
#     )

#     if choice == "Weather & best time":
#         st.write(state.get("weather_info", "Not available"))
#         st.markdown(
#             f"**🗓 Best time:** {state.get('best_time', 'Not available')}"
#         )

#     elif choice == "Destination":
#         st.write(state.get("place_info", "Not available"))

#     elif choice == "Transport":
#         st.write(state.get("transport_info", "Not available"))

#     elif choice == "Budget":
#         st.write(state.get("budget_info", "Not available"))

#     elif choice == "Final Itinerary":
#         st.write(state.get("final_itinerary", "Not available"))

#     if state.get("warnings"):
#         st.divider()
#         st.subheader("⚠️ Warnings")
#         for warning in state["warnings"]:
#             st.warning(warning)

#     # ── Replan Info ──────────────────────────────────────────────────────────
#     replan_msg = state.get("_replan_message", "")
#     if replan_msg:
#         st.divider()
#         st.subheader("♻️ Replan Info")
#         st.info(replan_msg)

#         changed = state.get("_changed_fields", [])
#         if changed:
#             st.markdown(f"**Changed:** `{'`, `'.join(changed)}`")

#         ran = state.get("_replan_agents", [])
#         all_agents = ["weather", "destination", "transport", "budget", "itinerary"]
#         skipped = [a for a in all_agents if a not in ran]
#         if ran:
#             st.markdown(f"**Ran:** `{'`, `'.join(ran)}`")
#         if skipped:
#             st.markdown(f"**Skipped (cached):** `{'`, `'.join(skipped)}`")

# # ---------------- Chat History ----------------
# for msg in st.session_state.chat_history:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # ---------------- Chat Input ----------------
# user_input = st.chat_input(
#     "Tell me about your trip... (e.g. 3-day trip to Goa in December, budget 30000)"
# )

# if user_input:

#     st.session_state.chat_history.append(
#         {"role": "user", "content": user_input}
#     )

#     with st.chat_message("user"):
#         st.markdown(user_input)

#     with st.chat_message("assistant"):
#         with st.spinner("Planning your trip..."):

#             # ── Snapshot of PREVIOUS trip params (before this turn's extraction) ──
#             prev_state = {
#                 k: st.session_state.trip_state.get(k)
#                 for k in ("trip_place", "trip_dates", "trip_days",
#                           "trip_budget", "trip_style",
#                           "weather_info", "place_info", "transport_info",
#                           "budget_info", "final_itinerary")
#             }

#             # ── Build current state for this turn ──
#             current = st.session_state.trip_state.copy()
#             current["user_input"] = user_input
#             current["chat_history"] = [
#                 m["content"]
#                 for m in st.session_state.chat_history[:-1]
#                 if m["role"] == "user"
#             ]
#             current["trace"] = []   # reset trace each turn

#             # ── Selective invocation ──
#             result, replan_msg = invoke_smart(current, prev_state)

#             st.session_state.trip_state = result

#             # ── Response message ──
#             if result.get("need_clarification"):
#                 response = (
#                     "Before I can plan this, could you tell me your "
#                     + ", ".join(result.get("missing_fields", []))
#                     + "?"
#                 )
#                 st.markdown(response)

#             elif result.get("final_itinerary"):
#                 ran_agents = result.get("_replan_agents", [])
#                 changed = result.get("_changed_fields", [])

#                 if changed:
#                     # Replanning happened
#                     label_map = {
#                         "trip_place":  "destination",
#                         "trip_dates":  "travel dates",
#                         "trip_days":   "trip duration",
#                         "trip_budget": "budget",
#                         "trip_style":  "trip style",
#                     }
#                     changed_readable = [label_map.get(f, f) for f in changed]
#                     response = (
#                         f"♻️ **Replanned!** Updated `{'`, `'.join(changed_readable)}`.\n\n"
#                         f"Re-ran agents: `{'`, `'.join(ran_agents)}`.\n\n"
#                         "✅ Trip plan updated! Scroll down for the new itinerary."
#                     )
#                 else:
#                     response = (
#                         "✅ Trip plan generated successfully! "
#                         "Scroll down to view the complete itinerary."
#                     )
#                 st.success(response)

#             else:
#                 response = (
#                     "I couldn't generate the itinerary yet. "
#                     "Please add more details."
#                 )
#                 st.warning(response)

#     st.session_state.chat_history.append(
#         {"role": "assistant", "content": response}
#     )

# # ---------------- Behind The Scenes ----------------
# trace = st.session_state.trip_state.get("trace", [])

# if trace:
#     with st.expander(
#         f"🔧 Behind the scenes — {len(trace)} tool / API calls"
#     ):
#         for step in trace:
#             st.markdown(
#                 f"**{step.get('step')}** · _{step.get('source')}_"
#             )
#             st.code(str(step.get("output"))[:1500])

# # ---------------- Final Itinerary ----------------
# st.divider()
# st.subheader("🗺 Final Trip Plan")

# if st.session_state.trip_state.get("final_itinerary"):
#     st.markdown(
#         st.session_state.trip_state["final_itinerary"]
#     )
# else:
#     st.info(
#         "Your itinerary will appear here after planning."
#     )

import streamlit as st
import re
from graph.workflow import invoke_smart

# --------------------------------------------------
# Page Config
# --------------------------------------------------
st.set_page_config(
    page_title="Smart Trip Planner",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ Smart Trip Planning Assistant")

# --------------------------------------------------
# ✅ Field Extraction (VERY IMPORTANT FIX)
# --------------------------------------------------
def extract_fields_from_text(text, state):
    text_lower = text.lower()

    # ✅ Budget Extraction
    budget_match = re.search(r'(\d{4,6})', text_lower)
    if budget_match:
        state["trip_budget"] = int(budget_match.group(1))

    # ✅ Days Extraction
    days_match = re.search(r'(\d+)[-\s]?day', text_lower)
    if days_match:
        state["trip_days"] = int(days_match.group(1))

    # ✅ Place Extraction (basic demo)
    places = ["mumbai", "goa", "delhi", "manali", "jaipur"]
    for p in places:
        if p in text_lower:
            state["trip_place"] = p.capitalize()

    # ✅ Month Extraction
    months = [
        "january","february","march","april","may","june",
        "july","august","september","october","november","december"
    ]
    for m in months:
        if m in text_lower:
            state["trip_dates"] = m.capitalize()

    return state

# --------------------------------------------------
# Session State
# --------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "trip_state" not in st.session_state:
    st.session_state.trip_state = {}

# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.header("🔍 Agent Outputs")

    state = st.session_state.trip_state

    choice = st.selectbox(
        "Select agent output:",
        [
            "Weather & best time",
            "Destination",
            "Transport",
            "Budget",
            "Final Itinerary",
        ],
    )

    if choice == "Weather & best time":
        st.write(state.get("weather_info", "Not available"))
        st.markdown(f"**🗓 Best time:** {state.get('best_time', 'Not available')}")

    elif choice == "Destination":
        st.write(state.get("place_info", "Not available"))

    elif choice == "Transport":
        st.write(state.get("transport_info", "Not available"))

    elif choice == "Budget":
        st.write(state.get("budget_info", "Not available"))

    elif choice == "Final Itinerary":
        st.write(state.get("final_itinerary", "Not available"))

    # ✅ Replan Info
    replan_msg = state.get("_replan_message", "")
    if replan_msg:
        st.divider()
        st.subheader("♻️ Replan Info")
        st.info(replan_msg)

        changed = state.get("_changed_fields", [])
        if changed:
            st.markdown(f"**Changed:** `{'`, `'.join(changed)}`")

        ran = state.get("_replan_agents", [])
        all_agents = ["weather", "destination", "transport", "budget", "itinerary"]
        skipped = [a for a in all_agents if a not in ran]

        if ran:
            st.markdown(f"**Ran:** `{'`, `'.join(ran)}`")
        if skipped:
            st.markdown(f"**Skipped:** `{'`, `'.join(skipped)}`")

# --------------------------------------------------
# Chat History Display
# --------------------------------------------------
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# Chat Input
# --------------------------------------------------
user_input = st.chat_input("Describe your trip...")

if user_input:

    # Show user message
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Planning your trip..."):

            # ✅ FULL previous state
            prev_state = st.session_state.trip_state.copy()

            # ✅ Build current state
            current = prev_state.copy()
            current["user_input"] = user_input

            # ✅ ✅ CRITICAL FIX: Extract BEFORE replan
            current = extract_fields_from_text(user_input, current)

            current["chat_history"] = [
                m["content"]
                for m in st.session_state.chat_history
                if m["role"] == "user"
            ]

            current["trace"] = []

            # ✅ Smart execution
            result, replan_msg = invoke_smart(current, prev_state)

            # ✅ Save state
            st.session_state.trip_state = result

            # --------------------------------------------------
            # Response Handling
            # --------------------------------------------------
            if result.get("need_clarification"):
                response = (
                    "Please provide: "
                    + ", ".join(result.get("missing_fields", []))
                )
                st.warning(response)

            elif result.get("final_itinerary"):

                changed = result.get("_changed_fields", [])
                ran_agents = result.get("_replan_agents", [])

                if changed:
                    label_map = {
                        "trip_place": "destination",
                        "trip_dates": "travel dates",
                        "trip_days": "trip duration",
                        "trip_budget": "budget",
                        "trip_style": "trip style",
                    }

                    readable = [label_map.get(f, f) for f in changed]

                    response = (
                        f"♻️ Replanned → Updated: `{'`, `'.join(readable)}`\n\n"
                        f"Agents run: `{'`, `'.join(ran_agents)}`\n\n"
                        f"✅ Trip updated!"
                    )
                else:
                    response = "✅ Trip plan generated!"

                st.success(response)

            else:
                response = "⚠️ Not enough info to generate plan."
                st.warning(response)

    # Save assistant response
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response
    })

# --------------------------------------------------
# Final Output
# --------------------------------------------------
st.divider()
st.subheader("🗺 Final Trip Plan")

if st.session_state.trip_state.get("final_itinerary"):
    st.markdown(st.session_state.trip_state["final_itinerary"])
else:
    st.info("Your itinerary will appear here.")