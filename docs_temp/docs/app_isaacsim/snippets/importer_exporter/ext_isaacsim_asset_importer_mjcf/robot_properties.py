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
