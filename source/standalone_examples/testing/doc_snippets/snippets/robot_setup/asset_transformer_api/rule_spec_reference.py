from isaacsim.asset.transformer import RuleSpec

rule_spec = RuleSpec(
    name="My Custom Transformation",
    type="my_extension.rules.MyCustomRule",
    destination="payloads",
    params={"my_param": "custom_value", "scope": "/World/Robot"},
    enabled=True,
)
