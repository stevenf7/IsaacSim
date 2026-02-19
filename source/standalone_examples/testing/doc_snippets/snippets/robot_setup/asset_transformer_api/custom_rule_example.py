from isaacsim.asset.transformer import RuleConfigurationParam, RuleInterface, RuleRegistry
from pxr import Usd


class MyCustomRule(RuleInterface):
    """A custom transformation rule."""

    def get_configuration_parameters(self) -> list[RuleConfigurationParam]:
        return [
            RuleConfigurationParam(
                name="my_param",
                display_name="My Parameter",
                param_type=str,
                description="Description of the parameter",
                default_value="default_value",
            ),
            RuleConfigurationParam(
                name="scope",
                display_name="Scope",
                param_type=str,
                description="Root prim path to process",
                default_value="/",
            ),
        ]

    def process_rule(self) -> str | None:
        params = self.args.get("params", {}) or {}
        my_param = params.get("my_param", "default_value")
        scope = params.get("scope", "/")

        self.log_operation(f"MyCustomRule start my_param={my_param} scope={scope}")
        stage = self.source_stage

        # Process prims within scope
        scope_prim = stage.GetPrimAtPath(scope)
        if not scope_prim.IsValid():
            self.log_operation(f"Scope prim not found: {scope}")
            return None

        processed_count = 0
        for prim in Usd.PrimRange(scope_prim):
            # Your transformation logic here
            processed_count += 1

        self.log_operation(f"Processed {processed_count} prim(s)")
        self.log_operation("MyCustomRule completed")
        self.add_affected_stage("my_output.usda")

        return None  # Continue with current working stage


# Register the rule with the singleton registry
registry = RuleRegistry()
registry.register(MyCustomRule)
