VARIABLES_TO_EXPOSE = [
    {
        "attr_name": "targetLocation",
        "attr_type": Sdf.ValueTypeNames.Vector3d,
        "default_value": Gf.Vec3d(0.0, 0.0, 0.0),
        "doc": "The 3D vector specifying the location to look at.",
    },
    {
        "attr_name": "targetPrimPath",
        "attr_type": Sdf.ValueTypeNames.String,
        "default_value": "",
        "doc": "The path of the target prim to look at. If specified, it has priority over the target location.",
    },
    # Additional variables...
]
