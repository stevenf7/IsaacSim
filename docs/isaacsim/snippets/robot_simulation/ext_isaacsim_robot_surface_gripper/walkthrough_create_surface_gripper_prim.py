# Create and configure a Surface Gripper prim under ee_link (same outcome as the GUI tab).
# Run with the Isaac Sim stage loaded; paths must match your robot and suction_joint from the walkthrough.

import omni.kit.commands
import omni.usd
import usd.schema.isaac.robot_schema as robot_schema
from pxr import Sdf

stage = omni.usd.get_context().get_stage()

# Parent Xform for the tool (same as in the walkthrough when the robot lives under /World/ur10).
ee_link_path = "/World/ur10/ee_link"
# D6 joint configured earlier under surface_gripper (see walkthrough).
suction_joint_path = f"{ee_link_path}/surface_gripper/suction_joint"

# Same as **Create** > **Isaac** > **Robots** > **Surface Gripper** with ee_link selected:
# the command creates a child prim named SurfaceGripper (or SurfaceGripper_01, … if needed).
_, gripper_prim = omni.kit.commands.execute("CreateSurfaceGripper", prim_path=ee_link_path)

# **Attachment Points** → suction_joint
attachment_points_rel = gripper_prim.GetRelationship(robot_schema.Relations.ATTACHMENT_POINTS.name)
attachment_points_rel.SetTargets([Sdf.Path(suction_joint_path)])

# **Max Grip Distance** = 0.01 (defaults for retry / force limits match the GUI until you tune them)
gripper_prim.GetAttribute(robot_schema.Attributes.MAX_GRIP_DISTANCE.name).Set(0.01)
