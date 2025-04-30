import json
import platform
import xml.etree.ElementTree as ET
from collections import defaultdict
from glob import glob

import packmanapi

# Detect platform
system = platform.system().lower()
if system == "linux":
    platform = "manylinux_2_35_x86_64"
    platform_target = "linux-x86_64"
elif system == "windows":
    platform = "windows-x86_64"
    platform_target = "windows-x86_64"
else:
    raise RuntimeError(f"Unsupported platform: {system}")

files = glob("./deps/*.packman.xml")
results_by_file = defaultdict(list)
deps_count_by_file = {}
json_output = {}

for file in files:
    # Parse XML to count dependencies
    tree = ET.parse(file)
    root = tree.getroot()
    total_deps = len(root.findall(".//dependency"))
    deps_count_by_file[file] = total_deps

    _, results = packmanapi.verify(
        file,
        exclude_local=True,
        remotes=["cloudfront"],
        tokens={"config": "release", "platform_target": platform_target, "platform_target_abi": platform_target},
        platform=platform,
        tags={"public": "true"},
    )

    print(f"Scanned {file} for packman dependencies, {len(results)} issue{'s' if len(results) != 1 else ''} found")

    results_by_file[file] = results

    # Prepare JSON output for this file
    json_output[file] = {
        "total_dependencies": total_deps,
        "issues_count": len(results),
        "problem_packages": [
            {"name": result[1].__dict__["name"], "version": result[1].__dict__["version"]} for result in results
        ],  # Extract package names from results
    }

total_issues = 0
total_deps = 0
print("\nSummary of issues:")
print("-" * 80)
for file in sorted(results_by_file.keys()):
    issues = results_by_file[file]
    total_issues += len(issues)
    total_deps += deps_count_by_file[file]
    print(f"\n{file}:")
    print(f"  {len(issues)} issue{'s' if len(issues) != 1 else ''} out of {deps_count_by_file[file]} dependencies")

print(f"\nTotal issues found: {total_issues} across {total_deps} total dependencies")

# Write JSON output
with open("packman_verification_results.json", "w") as f:
    json.dump(json_output, f, indent=2)

print("\nDetailed results written to packman_verification_results.json")

# If we have anything in here then we failed verification
exit(total_issues)
