_, sensor_2D = omni.kit.commands.execute(
    "IsaacSensorCreateRtxLidar",
    path="/sensor_2D",
    parent=None,
    config="Example_Rotary_2D",
    translation=(0, 0, 1.0),
    orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
)
