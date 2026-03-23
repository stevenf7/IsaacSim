# -- Test setup --
import omni.usd
from pxr import Sdf, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()

# Create a revolute joint to demonstrate mecanum wheel attributes
UsdGeom.Xform.Define(stage, "/World/robot")
UsdGeom.Xform.Define(stage, "/World/robot/wheel")
joint = UsdPhysics.RevoluteJoint.Define(stage, "/World/robot/wheel_joint")
# -- End test setup --

joint_prim = stage.GetPrimAtPath("/World/robot/wheel_joint")
joint_prim.CreateAttribute("isaacmecanumwheel:radius", Sdf.ValueTypeNames.Float).Set(0.12)
joint_prim.CreateAttribute("isaacmecanumwheel:angle", Sdf.ValueTypeNames.Float).Set(10.3)
