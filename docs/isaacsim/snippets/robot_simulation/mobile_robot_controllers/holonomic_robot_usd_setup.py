stage = omni.usd.get_context().get_stage()
joint_prim = stage.GetPrimAtPath("/path/to/wheel_joint")
joint_prim.CreateAttribute("isaacmecanumwheel:radius", Sdf.ValueTypeNames.Float).Set(0.12)
joint_prim.CreateAttribute("isaacmecanumwheel:angle", Sdf.ValueTypeNames.Float).Set(10.3)
