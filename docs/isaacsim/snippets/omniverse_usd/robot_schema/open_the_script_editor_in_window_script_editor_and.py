import omni.usd
from pxr import Usd, UsdGeom

# For legacy reasons, we need to import the schema from the usd.schema.isaac package
from usd.schema.isaac import robot_schema

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath("/World/ur10e")


robot_tree = robot_schema.utils.GenerateRobotLinkTree(stage, prim)

robot_schema.utils.PrintRobotTree(robot_tree)
