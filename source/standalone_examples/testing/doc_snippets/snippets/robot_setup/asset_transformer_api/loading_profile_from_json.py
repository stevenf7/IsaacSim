import json

from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile

# Load profile from JSON file
with open("/path/to/profile.json", "r") as f:
    profile_data = json.load(f)

profile = RuleProfile.from_dict(profile_data)

# Run transformation
manager = AssetTransformerManager()
report = manager.run(
    input_stage_path="/path/to/robot.usd",
    profile=profile,
    package_root="/output/robot_package",
)
