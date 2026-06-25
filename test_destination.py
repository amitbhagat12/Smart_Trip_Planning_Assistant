from agents.destination_agent import destination_agent

test_state = {
    "trip_place": "Goa",
    "trip_days": 3,
    "trip_style": "family",
    "trip_dates": "December",
    "warnings": [],
    "trace": []
}

result = destination_agent(test_state)

print("\nPLACE INFO:")
print(result.get("place_info"))

print("\nTRACE:")
print(result.get("trace"))

print("\nWARNINGS:")
print(result.get("warnings"))