"""Camera sensor creation and annotator attachment for Isaac Sim Replicator.

Creates a USD camera prim and attaches standard perception annotators
(RGB, depth, segmentation, bbox, normals, motion vectors).
"""


def create_camera_sensor(stage, path: str, focal_length: float = 24.0, resolution: tuple = (1280, 720)):
    """Define a USD camera prim and return its Replicator render product.

    Args:
        stage: The USD stage to add the camera to.
        path: USD prim path for the new camera (e.g. "/World/Camera").
        focal_length: Camera focal length in mm.
        resolution: Output resolution as (width, height).

    Returns:
        rep.RenderProduct handle.
    """
    import omni.replicator.core as rep
    from pxr import Gf, UsdGeom

    cam = UsdGeom.Camera.Define(stage, path)
    cam.GetFocalLengthAttr().Set(focal_length)
    cam.GetHorizontalApertureAttr().Set(36.0)
    cam.GetVerticalApertureAttr().Set(20.25)
    cam.GetClippingRangeAttr().Set(Gf.Vec2f(0.01, 100.0))
    return rep.create.render_product(path, resolution)


def attach_annotators(rp) -> dict:
    """Attach common perception annotators to a render product.

    Args:
        rp: Replicator render product handle.

    Returns:
        Dict mapping annotator name to annotator handle.
    """
    import omni.replicator.core as rep

    names = [
        "rgb",
        "distance_to_camera",
        "semantic_segmentation",
        "instance_segmentation",
        "motion_vectors",
        "bounding_box_2d_tight",
        "bounding_box_3d",
        "normals",
    ]
    ann = {}
    for n in names:
        init = {"colorize": True} if "segmentation" in n else {}
        ann[n] = rep.AnnotatorRegistry.get_annotator(n, init_params=init)
        ann[n].attach([rp])
    return ann
