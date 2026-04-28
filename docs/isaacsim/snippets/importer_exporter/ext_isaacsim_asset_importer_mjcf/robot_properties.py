# -- Test setup --
import omni.usd
from pxr import UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, "/carter")
UsdGeom.Xform.Define(stage, "/carter/chassis_link")
UsdGeom.Xform.Define(stage, "/carter/chassis_link/left_wheel")
UsdGeom.Xform.Define(stage, "/carter/chassis_link/right_wheel")
left_joint = UsdPhysics.RevoluteJoint.Define(stage, "/carter/chassis_link/left_wheel")
right_joint = UsdPhysics.RevoluteJoint.Define(stage, "/carter/chassis_link/right_wheel")
UsdPhysics.DriveAPI.Apply(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")
UsdPhysics.DriveAPI.Apply(stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular")
# -- End test setup --
# get handle to the Drive API for both wheels
left_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/left_wheel"), "angular")
right_wheel_drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath("/carter/chassis_link/right_wheel"), "angular")

# Set the velocity drive target in degrees/second
left_wheel_drive.GetTargetVelocityAttr().Set(150)
right_wheel_drive.GetTargetVelocityAttr().Set(150)

# Set the drive damping, which controls the strength of the velocity drive
left_wheel_drive.GetDampingAttr().Set(15000)
right_wheel_drive.GetDampingAttr().Set(15000)

# Set the drive stiffness, which controls the strength of the position drive
# In this case because we want to do velocity control this should be set to zero
left_wheel_drive.GetStiffnessAttr().Set(0)
right_wheel_drive.GetStiffnessAttr().Set(0)
