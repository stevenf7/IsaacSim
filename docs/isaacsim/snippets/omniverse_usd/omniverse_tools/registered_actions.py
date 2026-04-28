import omni.kit.actions.core

extension_id = "my.extension"
action_name = "my_action"
action_function_callable = lambda: None

action_registry = omni.kit.actions.core.get_action_registry()
action_registry.register_action(
    extension_id,
    action_name,
    action_function_callable,
)

# deregistered action at extension shutdown
action_registry.deregister_action(
    extension_id,
    action_name,
)
