from isaacsim.asset.transformer import RuleRegistry

registry = RuleRegistry()
rule_types = registry.list_rule_types()
for rule_type in rule_types:
    print(rule_type)

rule_cls = registry.get("isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule")
if rule_cls:
    temp_rule = rule_cls.__new__(rule_cls)
    temp_rule._log = []
    params = temp_rule.get_configuration_parameters()
    for param in params:
        print(f"  {param.name}: {param.param_type.__name__} = {param.default_value}")
