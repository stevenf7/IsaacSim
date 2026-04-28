# -- Test setup --
import omni.usd
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, "/World")
UsdGeom.Xform.Define(stage, "/World/Surface_Gripper_Joints")

for i in range(2):
    joint = UsdPhysics.Joint.Define(stage, f"/World/Surface_Gripper_Joints/joint_{i}")
# -- End test setup --

# [define-properties]
import usd.schema.isaac.robot_schema as robot_schema
from isaacsim.robot.surface_gripper import _surface_gripper as surface_gripper

gripper_prim_path = "/World/SurfaceGripper"
gripper_interface = surface_gripper.acquire_surface_gripper_interface()

# Create the Surface Gripper Prim
# Once it is created it can be saved and this doesn't need to be redone
robot_schema.CreateSurfaceGripper(stage, gripper_prim_path)
gripper_prim = stage.GetPrimAtPath(gripper_prim_path)
attachment_points_rel = gripper_prim.GetRelationship(robot_schema.Relations.ATTACHMENT_POINTS.name)

# Select the joints to the gripper
# The joints should be D6 joints defined in the usd file.
# All joint attributes can be defined as desired, except for:
# Joint Should be enabled
# Joint Type should be D6
# All Joint Parents should be the same Rigid body
# Exclude from Articulation must be checked
# No Break force/Torque should be set
# Joint drives can be used to derive the desired joint bounce/stretch behavior
# Enable/Disable the joint DoFs and limits as desired.

gripper_joints = [p.GetPath() for p in stage.GetPrimAtPath("/World/Surface_Gripper_Joints").GetChildren()]
attachment_points_rel.SetTargets(gripper_joints)

# Define the distance the joint can grasp, and at what distance from the origin of the joints it will settle
gripper_prim.GetAttribute(robot_schema.Attributes.MAX_GRIP_DISTANCE.name).Set(0.011)
# Define the Override Break limits
gripper_prim.GetAttribute(robot_schema.Attributes.COAXIAL_FORCE_LIMIT.name).Set(0.005)
gripper_prim.GetAttribute(robot_schema.Attributes.SHEAR_FORCE_LIMIT.name).Set(5)

# How long the gripper will try to close if it is open
gripper_prim.GetAttribute(robot_schema.Attributes.RETRY_INTERVAL.name).Set(1.0)
# [/define-properties]

# [get-state]
status = gripper_interface.get_gripper_status(gripper_prim_path)
print(status)  # Open, Closed, or Closing
# [/get-state]

# [control-gripper]
gripper_interface.close_gripper(gripper_prim_path)

gripper_interface.open_gripper(gripper_prim_path)

gripper_interface.set_gripper_action(gripper_prim_path, 0.5)  # Closes the gripper
gripper_interface.set_gripper_action(gripper_prim_path, -0.5)  # Opens the gripper
# [/control-gripper]
