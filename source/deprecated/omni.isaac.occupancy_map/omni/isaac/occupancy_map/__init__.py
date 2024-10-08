import carb

old_extension_name = "omni.isaac.occupancy_map"
new_extension_name = "isaacsim.asset.generator.occupancy_map"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)

from isaacsim.asset.generator.occupancy_map import *
