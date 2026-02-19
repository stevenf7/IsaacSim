# Iterate through rule results
for result in report.results:
    print(f"\n=== {result.rule.name} ===")
    print(f"Type: {result.rule.type}")
    print(f"Success: {result.success}")
    print(f"Duration: {result.started_at} to {result.finished_at}")
    print(f"Affected stages: {result.affected_stages}")

    # Print log entries
    print("Log:")
    for entry in result.log:
        print(f"  {entry['message']}")
