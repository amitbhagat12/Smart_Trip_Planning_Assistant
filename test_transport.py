from agents.transport_agent import transport_agentfrom agents.transport_agent import transport_agent/from city
    "source_place": "Mumbai",
    "start_location": "Mumbai",
    "from_place": "Mumbai",

    "warnings": [],
    "trace": []
}

result = transport_agent(test_state)

print("\nTRANSPORT INFO:")
print(result.get("transport_info"))

print("\nLOCAL TRANSPORT INFO:")
print(result.get("local_transport_info"))

print("\nTRACE:")
print(result.get("trace"))

print("\nWARNINGS:")
print(result.get("warnings"))

print("\nFULL UPDATED STATE:")
print(result)


test_state = {
    "trip_place": "Goa",
    "trip_days": 3,
    "trip_dates": "December",
    "trip_style": "family",

