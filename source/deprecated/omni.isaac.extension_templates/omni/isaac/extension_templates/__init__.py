import carb

old_extension_name = "omni.isaac.extension_templates"
new_extension_name = "isaacsim.examples.extension"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)

from isaacsim.examples.extension import *
