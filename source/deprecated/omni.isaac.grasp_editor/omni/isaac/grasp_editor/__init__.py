import carb

old_extension_name = "omni.isaac.grasp_editor"
new_extension_name = "isaacsim.robot_setup.grasp_editor"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)

from isaacsim.robot_setup.grasp_editor import *
