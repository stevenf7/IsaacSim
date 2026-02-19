from isaacsim.asset.transformer import AssetTransformerManager, RuleProfile

manager = AssetTransformerManager()

try:
    report = manager.run(input_stage_path, profile, package_root)
except RuntimeError as e:
    print(f"Transformation failed to start: {e}")
    # Raised if source stage cannot be opened or base export fails

# Check individual rule failures
for result in report.results:
    if not result.success:
        print(f"Rule '{result.rule.name}' failed: {result.error}")
