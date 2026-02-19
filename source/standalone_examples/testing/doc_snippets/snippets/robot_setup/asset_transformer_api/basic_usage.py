from isaacsim.asset.transformer import (
    AssetTransformerManager,
    RuleProfile,
    RuleSpec,
)

# Create a profile with rules
profile = RuleProfile(
    profile_name="My Transform Profile",
    version="1.0",
    rules=[
        RuleSpec(
            name="Route Physics Schemas",
            type="isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule",
            destination="payloads/Physics",
            params={
                "schemas": ["Physics*", "Physx*"],
                "stage_name": "physics.usda",
            },
            enabled=True,
        ),
        RuleSpec(
            name="Route Materials",
            type="isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule",
            destination="payloads",
            params={
                "materials_layer": "materials.usda",
                "deduplicate": True,
            },
            enabled=True,
        ),
    ],
)

# Create manager and run transformation
manager = AssetTransformerManager()
report = manager.run(
    input_stage_path="/path/to/robot.usd",
    profile=profile,
    package_root="/output/robot_package",
)

# Check results
print(f"Transform completed: {report.output_stage_path}")
for result in report.results:
    status = "SUCCESS" if result.success else "FAILED"
    print(f"  {result.rule.name}: {status}")
    if result.error:
        print(f"    Error: {result.error}")
