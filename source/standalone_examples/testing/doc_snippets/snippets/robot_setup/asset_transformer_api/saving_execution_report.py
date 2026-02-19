import json

# After running transformation
report = manager.run(input_stage_path, profile, package_root)

# Save report to JSON
report_path = f"{package_root}/transform_report.json"
with open(report_path, "w") as f:
    json.dump(report.to_dict(), f, indent=2)
